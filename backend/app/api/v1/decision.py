from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime
import uuid
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.models.ai_decision import AIDecision
from app.schemas.decision import (
    PurchaseEvaluationRequest,
    PurchaseEvaluationResponse,
    RiskAssessmentResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse
)
from app.services.jev_service import JevService
from app.services.finance_engine import FinanceEngine

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/evaluate-purchase", response_model=PurchaseEvaluationResponse)
async def evaluate_purchase(
    request: PurchaseEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Evaluate if a purchase is affordable using Jev decision layer.
    
    This is the core "Can I afford this?" feature.
    Returns a reasoned recommendation based on actual financial state.
    """
    jev_service = JevService()
    
    # Get dashboard data
    dashboard_data = await FinanceEngine.calculate_dashboard_state(db, current_user.id)
    
    if "error" in dashboard_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=dashboard_data["error"]
        )
    
    # Evaluate purchase using Jev
    decision = await jev_service.evaluate_purchase(
        request.amount,
        request.category,
        dashboard_data
    )
    
    # Log the decision
    ai_decision = AIDecision(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        decision_type="purchase_evaluation",
        input_context={
            "amount": request.amount,
            "category": request.category,
            "description": request.description
        },
        decision=decision.decision,
        confidence=decision.confidence,
        reasoning=decision.reasoning,
        model="jev" if jev_service.api_key else "rule_based"
    )
    
    db.add(ai_decision)
    await db.commit()
    
    # Prepare response with facts
    facts = {
        "remaining_flexible_budget": dashboard_data.get("remaining_flexible_budget", 0),
        "daily_budget": dashboard_data.get("daily_budget", 0),
        "remaining_days": dashboard_data.get("remaining_days", 0),
        "spending_velocity": dashboard_data.get("spending_velocity", 0),
        "budget_utilization": dashboard_data.get("budget_utilization", 0)
    }
    
    return PurchaseEvaluationResponse(
        decision=decision.decision,
        confidence=decision.confidence,
        reasoning=decision.reasoning,
        remaining_budget=decision.remaining_budget,
        facts=facts
    )


@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current spending risk assessment using Jev.
    
    Evaluates overall spending risk based on:
    - Budget utilization
    - Spending velocity vs target
    - Projected month-end balance
    - Recent spending patterns
    """
    jev_service = JevService()
    
    # Get dashboard data
    dashboard_data = await FinanceEngine.calculate_dashboard_state(db, current_user.id)
    
    if "error" in dashboard_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=dashboard_data["error"]
        )
    
    # Get recent expenses
    result = await db.execute(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.date.desc())
        .limit(10)
    )
    recent_expenses = result.scalars().all()
    
    # Evaluate risk using Jev
    risk_assessment = await jev_service.evaluate_spending_risk(
        dashboard_data,
        [{"amount": e.amount, "category": e.category, "date": str(e.date)} for e in recent_expenses]
    )
    
    # Log the decision
    ai_decision = AIDecision(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        decision_type="risk_assessment",
        input_context={"dashboard_data": dashboard_data},
        decision=risk_assessment.risk_level,
        confidence=risk_assessment.confidence,
        reasoning=f"Risk factors: {', '.join(risk_assessment.factors)}",
        model="jev" if jev_service.api_key else "rule_based"
    )
    
    db.add(ai_decision)
    await db.commit()
    
    # Prepare dashboard summary
    dashboard_summary = {
        "budget_utilization": dashboard_data.get("budget_utilization", 0),
        "spending_velocity": dashboard_data.get("spending_velocity", 0),
        "daily_budget": dashboard_data.get("daily_budget", 0),
        "remaining_days": dashboard_data.get("remaining_days", 0),
        "health_status": dashboard_data.get("health_status", "unknown")
    }
    
    return RiskAssessmentResponse(
        risk_level=risk_assessment.risk_level,
        confidence=risk_assessment.confidence,
        factors=risk_assessment.factors,
        dashboard_summary=dashboard_summary
    )


@router.post("/detect-anomaly", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Detect if an expense is anomalous using Jev.
    
    Compares the expense against historical spending in the same category.
    """
    jev_service = JevService()
    
    # Get category history
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(Expense)
        .where(
            Expense.user_id == current_user.id,
            Expense.category == request.category,
            Expense.date >= thirty_days_ago
        )
        .order_by(Expense.date.desc())
    )
    category_history = result.scalars().all()
    
    # Prepare expense data
    expense_data = {
        "amount": request.amount,
        "category": request.category,
        "description": request.description
    }
    
    # Detect anomaly using Jev
    anomaly = await jev_service.detect_anomaly(
        expense_data,
        [{"amount": e.amount, "date": str(e.date)} for e in category_history]
    )
    
    # Log the decision
    ai_decision = AIDecision(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        decision_type="anomaly_detection",
        input_context={"expense": expense_data, "history_count": len(category_history)},
        decision="anomaly" if anomaly.is_anomaly else "normal",
        confidence=anomaly.confidence,
        reasoning=anomaly.explanation,
        model="jev" if jev_service.api_key else "rule_based"
    )
    
    db.add(ai_decision)
    await db.commit()
    
    return AnomalyDetectionResponse(
        is_anomaly=anomaly.is_anomaly,
        anomaly_type=anomaly.anomaly_type,
        confidence=anomaly.confidence,
        explanation=anomaly.explanation
    )

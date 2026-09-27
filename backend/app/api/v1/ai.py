from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.ai import ParseExpenseRequest, ParseExpenseResponse, ChatRequest, ChatResponse, InsightResponse
from app.services.llm_service import LLMService
from app.services.finance_engine import FinanceEngine
from datetime import datetime, date

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/parse-expense", response_model=ParseExpenseResponse)
async def parse_expense(
    request: ParseExpenseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parse natural language expense text into structured data.
    
    Examples:
    - "₹150 lunch" → amount: 150, category: Food
    - "spent 80 on auto" → amount: 80, category: Transport
    - "I spent 200 on snacks" → amount: 200, category: Food
    """
    llm_service = LLMService()
    
    try:
        parsed = await llm_service.parse_expense(request.text)
        return ParseExpenseResponse(
            amount=parsed.amount,
            category=parsed.category,
            subcategory=parsed.subcategory,
            description=parsed.description,
            confidence=parsed.confidence
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse expense: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI chat interface for financial questions.
    
    The AI uses tools to retrieve actual financial data before answering.
    Available tools:
    - get_monthly_expenses
    - get_category_expenses
    - get_today_spending
    - get_budget_status
    - check_purchase
    """
    llm_service = LLMService()
    
    # Define available tools
    tools = {
        "get_monthly_expenses": "Get total expenses for current month",
        "get_category_expenses": "Get spending by category",
        "get_today_spending": "Get today's total spending",
        "get_budget_status": "Get current budget status",
        "check_purchase": "Check if a purchase is affordable"
    }
    
    try:
        if request.tool_results:
            # Generate response from tool results
            response = llm_service._generate_response_from_results(
                request.message,
                request.tool_results,
                tools
            )
            return ChatResponse(response=response, tool_calls=None)
        else:
            # Determine which tools to call
            tool_decision = await llm_service._determine_tool_needs(request.message, tools)
            
            if tool_decision.startswith("tool:"):
                # Parse tool call
                parts = tool_decision.split(":")
                tool_name = parts[1]
                tool_arg = parts[2] if len(parts) > 2 else None
                
                # Execute the tool
                tool_result = await execute_tool(tool_name, tool_arg, current_user.id, db)
                
                return ChatResponse(
                    response=llm_service._generate_response_from_results(
                        request.message,
                        {tool_name: tool_result},
                        tools
                    ),
                    tool_calls=None
                )
            else:
                # Direct response without tools
                return ChatResponse(response=tool_decision, tool_calls=None)
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


async def execute_tool(tool_name: str, tool_arg: Any, user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Execute a tool and return results."""
    today = date.today()
    
    if tool_name == "get_monthly_expenses":
        total = await FinanceEngine.get_variable_expenses_total(db, user_id, today.month, today.year)
        return {"total": total}
    
    elif tool_name == "get_category_expenses":
        if tool_arg:
            # Get specific category
            result = await db.execute(
                select(Expense.category, Expense.amount)
                .where(
                    Expense.user_id == user_id,
                    Expense.category == tool_arg,
                    Expense.date >= datetime(today.year, today.month, 1)
                )
            )
            expenses = result.all()
            total = sum(exp[1] for exp in expenses)
            return {"total": total, "category": tool_arg}
        else:
            # Get all categories
            breakdown = await FinanceEngine.get_category_breakdown(db, user_id, today.month, today.year)
            return {"categories": breakdown}
    
    elif tool_name == "get_today_spending":
        total = await FinanceEngine.get_today_spending(db, user_id)
        return {"total": total}
    
    elif tool_name == "get_budget_status":
        dashboard = await FinanceEngine.calculate_dashboard_state(db, user_id)
        return {
            "remaining": dashboard.get("remaining_flexible_budget", 0),
            "daily_budget": dashboard.get("daily_budget", 0),
            "utilization": dashboard.get("budget_utilization", 0)
        }
    
    elif tool_name == "check_purchase":
        if tool_arg:
            try:
                amount = float(tool_arg)
                dashboard = await FinanceEngine.calculate_dashboard_state(db, user_id)
                remaining = dashboard.get("remaining_flexible_budget", 0)
                
                # Simple decision logic (Phase 3 will use Jev)
                if amount <= remaining * 0.2:
                    decision = "ALLOW"
                elif amount <= remaining * 0.5:
                    decision = "CAUTION"
                else:
                    decision = "REVIEW"
                
                return {
                    "decision": decision,
                    "remaining_budget": remaining - amount,
                    "amount": amount
                }
            except ValueError:
                return {"error": "Invalid amount"}
    
    return {"error": "Unknown tool"}


@router.get("/insights", response_model=InsightResponse)
async def get_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered spending insights based on actual data."""
    llm_service = LLMService()
    
    # Get dashboard data
    dashboard_data = await FinanceEngine.calculate_dashboard_state(db, current_user.id)
    
    # Get recent expenses
    result = await db.execute(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.date.desc())
        .limit(10)
    )
    recent_expenses = result.scalars().all()
    
    # Generate insights
    insights = await llm_service.generate_spending_insights(
        dashboard_data,
        [{"amount": e.amount, "category": e.category, "description": e.description} for e in recent_expenses]
    )
    
    return InsightResponse(insights=insights)

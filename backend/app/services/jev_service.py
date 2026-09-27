from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import settings
import httpx
import json
from datetime import datetime


class ExpenseCategory(BaseModel):
    """Expense categorization decision."""
    category: str = Field(description="Primary category")
    subcategory: Optional[str] = Field(description="Subcategory if applicable")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)


class SpendingRisk(BaseModel):
    """Spending risk assessment."""
    risk_level: str = Field(description="Risk level: low, medium, high")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    factors: list[str] = Field(description="Factors contributing to risk assessment")


class PurchaseDecision(BaseModel):
    """Purchase evaluation decision."""
    decision: str = Field(description="Decision: ALLOW, CAUTION, REVIEW")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    reasoning: str = Field(description="Explanation for the decision")
    remaining_budget: float = Field(description="Budget after purchase")


class AnomalyDetection(BaseModel):
    """Expense anomaly detection."""
    is_anomaly: bool = Field(description="Whether expense is anomalous")
    anomaly_type: Optional[str] = Field(description="Type of anomaly if detected")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    explanation: str = Field(description="Explanation of anomaly")


class JevService:
    """Service for Jev AI decision layer.
    
    Jev handles bounded decisions with structured outputs:
    - Expense categorization
    - Spending risk assessment
    - Purchase evaluation
    - Anomaly detection
    
    All decisions are validated with Pydantic models.
    """

    def __init__(self):
        self.api_key = settings.JEV_API_KEY
        self.api_url = settings.JEV_API_URL

    async def classify_expense(self, description: str, amount: float) -> ExpenseCategory:
        """Classify expense into category using Jev.
        
        Args:
            description: Expense description
            amount: Expense amount
            
        Returns:
            ExpenseCategory with classification
        """
        categories = [
            "Food", "Transport", "Shopping", "Bills",
            "Entertainment", "Health", "Education",
            "Subscriptions", "Personal", "Other"
        ]
        
        # If Jev API is not configured, use rule-based fallback
        if not self.api_key:
            return self._classify_with_rules(description, amount)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/classify",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "description": description,
                        "amount": amount,
                        "categories": categories
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ExpenseCategory(**data)
                else:
                    return self._classify_with_rules(description, amount)
        except Exception:
            return self._classify_with_rules(description, amount)

    def _classify_with_rules(self, description: str, amount: float) -> ExpenseCategory:
        """Rule-based fallback for expense classification."""
        desc_lower = description.lower()
        
        category_map = {
            'Food': ['food', 'lunch', 'dinner', 'breakfast', 'snack', 'coffee', 'tea', 'restaurant', 'cafe', 'meal'],
            'Transport': ['auto', 'taxi', 'uber', 'ola', 'bus', 'train', 'metro', 'petrol', 'fuel', 'parking'],
            'Shopping': ['shop', 'clothes', 'dress', 'shoes', 'amazon', 'flipkart', 'mall'],
            'Bills': ['bill', 'electricity', 'water', 'internet', 'phone', 'recharge'],
            'Entertainment': ['movie', 'cinema', 'netflix', 'spotify', 'game', 'concert'],
            'Health': ['medicine', 'doctor', 'hospital', 'pharmacy', 'gym', 'fitness'],
            'Education': ['book', 'course', 'class', 'tuition', 'exam'],
            'Subscriptions': ['subscription', 'membership', 'plan'],
        }
        
        category = "Other"
        for cat, keywords in category_map.items():
            if any(keyword in desc_lower for keyword in keywords):
                category = cat
                break
        
        return ExpenseCategory(
            category=category,
            subcategory=None,
            confidence=0.75
        )

    async def evaluate_spending_risk(
        self,
        dashboard_data: Dict[str, Any],
        recent_expenses: list
    ) -> SpendingRisk:
        """Evaluate spending risk using Jev.
        
        Args:
            dashboard_data: Dashboard state from finance engine
            recent_expenses: Recent expense records
            
        Returns:
            SpendingRisk assessment
        """
        # If Jev API is not configured, use rule-based fallback
        if not self.api_key:
            return self._evaluate_risk_with_rules(dashboard_data, recent_expenses)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/evaluate-risk",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "dashboard_data": dashboard_data,
                        "recent_expenses": recent_expenses
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return SpendingRisk(**data)
                else:
                    return self._evaluate_risk_with_rules(dashboard_data, recent_expenses)
        except Exception:
            return self._evaluate_risk_with_rules(dashboard_data, recent_expenses)

    def _evaluate_risk_with_rules(
        self,
        dashboard_data: Dict[str, Any],
        recent_expenses: list
    ) -> SpendingRisk:
        """Rule-based fallback for risk assessment."""
        factors = []
        risk_score = 0
        
        # Factor 1: Budget utilization
        utilization = dashboard_data.get('budget_utilization', 0)
        if utilization > 90:
            risk_score += 3
            factors.append("High budget utilization")
        elif utilization > 75:
            risk_score += 2
            factors.append("Elevated budget utilization")
        
        # Factor 2: Spending velocity vs target
        velocity = dashboard_data.get('spending_velocity', 0)
        daily_budget = dashboard_data.get('daily_budget', 0)
        if velocity > daily_budget * 1.5:
            risk_score += 3
            factors.append("Spending significantly above daily target")
        elif velocity > daily_budget * 1.2:
            risk_score += 2
            factors.append("Spending above daily target")
        
        # Factor 3: Projected balance
        projected = dashboard_data.get('projected_month_end_balance', 0)
        if projected < 0:
            risk_score += 3
            factors.append("Projected overspending")
        elif projected < daily_budget * 3:
            risk_score += 1
            factors.append("Low projected balance")
        
        # Determine risk level
        if risk_score >= 6:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        confidence = min(0.9, 0.6 + (risk_score * 0.1))
        
        return SpendingRisk(
            risk_level=risk_level,
            confidence=confidence,
            factors=factors if factors else ["Spending within normal limits"]
        )

    async def evaluate_purchase(
        self,
        amount: float,
        category: str,
        dashboard_data: Dict[str, Any]
    ) -> PurchaseDecision:
        """Evaluate if a purchase is affordable using Jev.
        
        Args:
            amount: Purchase amount
            category: Purchase category
            dashboard_data: Dashboard state
            
        Returns:
            PurchaseDecision with recommendation
        """
        # If Jev API is not configured, use rule-based fallback
        if not self.api_key:
            return self._evaluate_purchase_with_rules(amount, category, dashboard_data)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/evaluate-purchase",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "amount": amount,
                        "category": category,
                        "dashboard_data": dashboard_data
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return PurchaseDecision(**data)
                else:
                    return self._evaluate_purchase_with_rules(amount, category, dashboard_data)
        except Exception:
            return self._evaluate_purchase_with_rules(amount, category, dashboard_data)

    def _evaluate_purchase_with_rules(
        self,
        amount: float,
        category: str,
        dashboard_data: Dict[str, Any]
    ) -> PurchaseDecision:
        """Rule-based fallback for purchase evaluation."""
        remaining = dashboard_data.get('remaining_flexible_budget', 0)
        daily_budget = dashboard_data.get('daily_budget', 0)
        remaining_days = dashboard_data.get('remaining_days', 1)
        
        # Calculate percentage of remaining budget
        if remaining > 0:
            percentage = (amount / remaining) * 100
        else:
            percentage = 100
        
        # Determine decision
        if amount > remaining:
            decision = "REVIEW"
            reasoning = f"This purchase (₹{amount:.0f}) exceeds your remaining flexible budget of ₹{remaining:.0f}."
            confidence = 0.95
        elif percentage > 50:
            decision = "REVIEW"
            reasoning = f"This purchase would use {percentage:.0f}% of your remaining budget. Consider if it's essential."
            confidence = 0.85
        elif percentage > 20:
            decision = "CAUTION"
            reasoning = f"This purchase would use {percentage:.0f}% of your remaining budget of ₹{remaining:.0f}. You have {remaining_days} days remaining."
            confidence = 0.80
        elif amount > daily_budget * 2:
            decision = "CAUTION"
            reasoning = f"This purchase is more than 2x your daily budget of ₹{daily_budget:.0f}."
            confidence = 0.75
        else:
            decision = "ALLOW"
            reasoning = f"This purchase is within your budget. You'll have ₹{remaining - amount:.0f} remaining after this purchase."
            confidence = 0.90
        
        return PurchaseDecision(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            remaining_budget=max(0, remaining - amount)
        )

    async def detect_anomaly(
        self,
        expense: Dict[str, Any],
        category_history: list
    ) -> AnomalyDetection:
        """Detect if an expense is anomalous using Jev.
        
        Args:
            expense: Expense to check
            category_history: Historical expenses in same category
            
        Returns:
            AnomalyDetection result
        """
        # If Jev API is not configured, use rule-based fallback
        if not self.api_key:
            return self._detect_anomaly_with_rules(expense, category_history)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/detect-anomaly",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "expense": expense,
                        "category_history": category_history
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return AnomalyDetection(**data)
                else:
                    return self._detect_anomaly_with_rules(expense, category_history)
        except Exception:
            return self._detect_anomaly_with_rules(expense, category_history)

    def _detect_anomaly_with_rules(
        self,
        expense: Dict[str, Any],
        category_history: list
    ) -> AnomalyDetection:
        """Rule-based fallback for anomaly detection."""
        amount = expense.get('amount', 0)
        category = expense.get('category', 'Other')
        
        if not category_history:
            return AnomalyDetection(
                is_anomaly=False,
                anomaly_type=None,
                confidence=0.5,
                explanation="No historical data for comparison"
            )
        
        # Calculate average and standard deviation
        amounts = [e.get('amount', 0) for e in category_history]
        avg_amount = sum(amounts) / len(amounts)
        
        # Check if amount is significantly higher than average
        if amount > avg_amount * 3:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_type="high_amount",
                confidence=0.85,
                explanation=f"This expense (₹{amount:.0f}) is more than 3x your average {category.lower()} spending of ₹{avg_amount:.0f}."
            )
        elif amount > avg_amount * 2:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_type="elevated_amount",
                confidence=0.70,
                explanation=f"This expense (₹{amount:.0f}) is more than 2x your average {category.lower()} spending of ₹{avg_amount:.0f}."
            )
        else:
            return AnomalyDetection(
                is_anomaly=False,
                anomaly_type=None,
                confidence=0.80,
                explanation="This expense is within normal range for this category."
            )

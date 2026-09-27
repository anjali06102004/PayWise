from datetime import datetime, date
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.expense import Expense
from app.models.fixed_expense import FixedExpense
from app.models.financial_profile import FinancialProfile


class FinanceEngine:
    """Deterministic financial calculation engine.
    
    All financial calculations are performed here using Python code.
    Never use LLMs for authoritative financial calculations.
    """

    @staticmethod
    async def get_financial_profile(db: AsyncSession, user_id: str) -> Optional[FinancialProfile]:
        """Get user's financial profile."""
        result = await db.execute(
            select(FinancialProfile).where(FinancialProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_fixed_expenses_total(db: AsyncSession, user_id: str) -> float:
        """Calculate total fixed expenses."""
        result = await db.execute(
            select(func.sum(FixedExpense.amount))
            .where(and_(FixedExpense.user_id == user_id, FixedExpense.is_active == True))
        )
        total = result.scalar()
        return total if total is not None else 0.0

    @staticmethod
    async def get_variable_expenses_total(
        db: AsyncSession, user_id: str, month: int, year: int
    ) -> float:
        """Calculate total variable expenses for a specific month."""
        result = await db.execute(
            select(func.sum(Expense.amount))
            .where(
                and_(
                    Expense.user_id == user_id,
                    func.extract('month', Expense.date) == month,
                    func.extract('year', Expense.date) == year
                )
            )
        )
        total = result.scalar()
        return total if total is not None else 0.0

    @staticmethod
    async def get_today_spending(db: AsyncSession, user_id: str) -> float:
        """Calculate total spending for today."""
        today = date.today()
        result = await db.execute(
            select(func.sum(Expense.amount))
            .where(
                and_(
                    Expense.user_id == user_id,
                    func.date(Expense.date) == today
                )
            )
        )
        total = result.scalar()
        return total if total is not None else 0.0

    @staticmethod
    def calculate_remaining_days() -> int:
        """Calculate remaining days in current month."""
        today = date.today()
        if today.month == 12:
            last_day = date(today.year + 1, 1, 1)
        else:
            last_day = date(today.year, today.month + 1, 1)
        
        return (last_day - today).days

    @staticmethod
    def calculate_flexible_budget(
        monthly_income: float,
        fixed_expenses: float,
        savings_goal: float
    ) -> float:
        """Calculate flexible spending budget."""
        return max(0, monthly_income - fixed_expenses - savings_goal)

    @staticmethod
    def calculate_remaining_flexible_budget(
        flexible_budget: float,
        variable_expenses: float
    ) -> float:
        """Calculate remaining flexible budget."""
        return max(0, flexible_budget - variable_expenses)

    @staticmethod
    def calculate_daily_budget(remaining_flexible_budget: float, remaining_days: int) -> float:
        """Calculate recommended daily spending budget."""
        if remaining_days <= 0:
            return 0.0
        return remaining_flexible_budget / remaining_days

    @staticmethod
    def calculate_weekly_budget(remaining_flexible_budget: float, remaining_days: int) -> float:
        """Calculate recommended weekly spending budget."""
        weeks = remaining_days / 7
        if weeks <= 0:
            return 0.0
        return remaining_flexible_budget / weeks

    @staticmethod
    def calculate_budget_utilization(
        flexible_budget: float,
        variable_expenses: float
    ) -> float:
        """Calculate budget utilization as percentage."""
        if flexible_budget == 0:
            return 0.0
        return (variable_expenses / flexible_budget) * 100

    @staticmethod
    def calculate_spending_velocity(
        variable_expenses: float,
        days_passed: int
    ) -> float:
        """Calculate average daily spending."""
        if days_passed <= 0:
            return 0.0
        return variable_expenses / days_passed

    @staticmethod
    def calculate_projected_month_end_balance(
        remaining_flexible_budget: float,
        daily_spending: float,
        remaining_days: int
    ) -> float:
        """Project month-end balance based on current spending velocity."""
        projected_spending = daily_spending * remaining_days
        return max(0, remaining_flexible_budget - projected_spending)

    @staticmethod
    async def get_category_breakdown(
        db: AsyncSession, user_id: str, month: int, year: int
    ) -> Dict[str, float]:
        """Get spending breakdown by category."""
        result = await db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(
                and_(
                    Expense.user_id == user_id,
                    func.extract('month', Expense.date) == month,
                    func.extract('year', Expense.date) == year
                )
            )
            .group_by(Expense.category)
        )
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def get_daily_spending_history(
        db: AsyncSession, user_id: str, days: int = 7
    ) -> List[Dict[str, any]]:
        """Get daily spending history for the last N days."""
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        result = await db.execute(
            select(func.date(Expense.date), func.sum(Expense.amount))
            .where(
                and_(
                    Expense.user_id == user_id,
                    func.date(Expense.date) >= start_date,
                    func.date(Expense.date) <= end_date
                )
            )
            .group_by(func.date(Expense.date))
            .order_by(func.date(Expense.date))
        )
        
        return [{"date": str(row[0]), "amount": row[1]} for row in result.all()]

    @staticmethod
    def get_spending_health_status(
        budget_utilization: float,
        daily_spending: float,
        recommended_daily: float
    ) -> str:
        """Determine spending health status.
        
        Returns: 'on_track', 'caution', 'high_spending'
        """
        if budget_utilization > 90:
            return "high_spending"
        elif daily_spending > recommended_daily * 1.3:
            return "high_spending"
        elif daily_spending > recommended_daily * 1.1:
            return "caution"
        elif budget_utilization > 75:
            return "caution"
        else:
            return "on_track"

    @staticmethod
    async def calculate_dashboard_state(db: AsyncSession, user_id: str) -> Dict:
        """Calculate complete dashboard state."""
        today = date.today()
        days_passed = today.day
        remaining_days = FinanceEngine.calculate_remaining_days()
        
        # Get financial profile
        profile = await FinanceEngine.get_financial_profile(db, user_id)
        if not profile:
            return {"error": "Financial profile not found"}
        
        # Calculate totals
        fixed_expenses = await FinanceEngine.get_fixed_expenses_total(db, user_id)
        variable_expenses = await FinanceEngine.get_variable_expenses_total(
            db, user_id, today.month, today.year
        )
        today_spending = await FinanceEngine.get_today_spending(db, user_id)
        
        # Calculate budgets
        flexible_budget = FinanceEngine.calculate_flexible_budget(
            profile.monthly_income,
            fixed_expenses,
            profile.savings_goal
        )
        remaining_flexible = FinanceEngine.calculate_remaining_flexible_budget(
            flexible_budget,
            variable_expenses
        )
        daily_budget = FinanceEngine.calculate_daily_budget(
            remaining_flexible,
            remaining_days
        )
        weekly_budget = FinanceEngine.calculate_weekly_budget(
            remaining_flexible,
            remaining_days
        )
        
        # Calculate metrics
        budget_utilization = FinanceEngine.calculate_budget_utilization(
            flexible_budget,
            variable_expenses
        )
        spending_velocity = FinanceEngine.calculate_spending_velocity(
            variable_expenses,
            days_passed
        )
        projected_balance = FinanceEngine.calculate_projected_month_end_balance(
            remaining_flexible,
            spending_velocity,
            remaining_days
        )
        
        # Get category breakdown
        category_breakdown = await FinanceEngine.get_category_breakdown(
            db, user_id, today.month, today.year
        )
        
        # Determine health status
        health_status = FinanceEngine.get_spending_health_status(
            budget_utilization,
            spending_velocity,
            daily_budget
        )
        
        return {
            "monthly_income": profile.monthly_income,
            "fixed_expenses": fixed_expenses,
            "savings_goal": profile.savings_goal,
            "flexible_budget": flexible_budget,
            "variable_expenses": variable_expenses,
            "remaining_flexible_budget": remaining_flexible,
            "today_spending": today_spending,
            "daily_budget": daily_budget,
            "weekly_budget": weekly_budget,
            "budget_utilization": budget_utilization,
            "spending_velocity": spending_velocity,
            "projected_month_end_balance": projected_balance,
            "remaining_days": remaining_days,
            "days_passed": days_passed,
            "category_breakdown": category_breakdown,
            "health_status": health_status,
            "currency": profile.currency
        }

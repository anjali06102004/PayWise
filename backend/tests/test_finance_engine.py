import pytest
from app.services.finance_engine import FinanceEngine


class TestFinanceEngine:
    """Tests for the deterministic finance engine."""
    
    def test_calculate_flexible_budget(self):
        """Test flexible budget calculation."""
        income = 20000
        fixed = 12000
        savings = 5000
        
        result = FinanceEngine.calculate_flexible_budget(income, fixed, savings)
        
        assert result == 3000
    
    def test_calculate_flexible_budget_zero(self):
        """Test flexible budget when expenses exceed income."""
        income = 10000
        fixed = 8000
        savings = 3000
        
        result = FinanceEngine.calculate_flexible_budget(income, fixed, savings)
        
        assert result == 0  # Should not go negative
    
    def test_calculate_flexible_budget_no_savings(self):
        """Test flexible budget with no savings goal."""
        income = 20000
        fixed = 12000
        savings = 0
        
        result = FinanceEngine.calculate_flexible_budget(income, fixed, savings)
        
        assert result == 8000
    
    def test_calculate_daily_budget(self):
        """Test daily budget calculation."""
        remaining = 3000
        days = 30
        
        result = FinanceEngine.calculate_daily_budget(remaining, days)
        
        assert result == 100
    
    def test_calculate_daily_budget_zero_days(self):
        """Test daily budget with zero days remaining."""
        remaining = 3000
        days = 0
        
        result = FinanceEngine.calculate_daily_budget(remaining, days)
        
        assert result == 0  # Should handle zero division
    
    def test_calculate_budget_utilization(self):
        """Test budget utilization percentage."""
        flexible_budget = 3000
        variable_expenses = 1500
        
        result = FinanceEngine.calculate_budget_utilization(flexible_budget, variable_expenses)
        
        assert result == 50.0
    
    def test_calculate_budget_utilization_zero_budget(self):
        """Test budget utilization with zero budget."""
        flexible_budget = 0
        variable_expenses = 1500
        
        result = FinanceEngine.calculate_budget_utilization(flexible_budget, variable_expenses)
        
        assert result == 100.0  # Should be 100% when budget is zero
    
    def test_get_spending_health_status_on_track(self):
        """Test spending health status - on track."""
        utilization = 60
        daily_spending = 120
        daily_budget = 100
        
        result = FinanceEngine.get_spending_health_status(
            utilization, daily_spending, daily_budget
        )
        
        assert result == "on_track"
    
    def test_get_spending_health_status_caution(self):
        """Test spending health status - caution."""
        utilization = 80
        daily_spending = 120
        daily_budget = 100
        
        result = FinanceEngine.get_spending_health_status(
            utilization, daily_spending, daily_budget
        )
        
        assert result == "caution"
    
    def test_get_spending_health_status_high_spending(self):
        """Test spending health status - high spending."""
        utilization = 95
        daily_spending = 150
        daily_budget = 100
        
        result = FinanceEngine.get_spending_health_status(
            utilization, daily_spending, daily_budget
        )
        
        assert result == "high_spending"
    
    def test_calculate_spending_velocity(self):
        """Test spending velocity calculation."""
        total_spent = 1500
        days_passed = 10
        
        result = FinanceEngine.calculate_spending_velocity(total_spent, days_passed)
        
        assert result == 150
    
    def test_calculate_spending_velocity_zero_days(self):
        """Test spending velocity with zero days."""
        total_spent = 1500
        days_passed = 0
        
        result = FinanceEngine.calculate_spending_velocity(total_spent, days_passed)
        
        assert result == 0  # Should handle zero division
    
    def test_calculate_projected_month_end_balance(self):
        """Test projected month-end balance."""
        remaining_budget = 3000
        spending_velocity = 150
        remaining_days = 10
        
        result = FinanceEngine.calculate_projected_month_end_balance(
            remaining_budget, spending_velocity, remaining_days
        )
        
        assert result == 1500  # 3000 - (150 * 10)

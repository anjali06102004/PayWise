from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FinancialProfileBase(BaseModel):
    monthly_income: float
    savings_goal: float
    currency: str = "INR"


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileUpdate(FinancialProfileBase):
    pass


class FinancialProfileResponse(FinancialProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FixedExpenseBase(BaseModel):
    name: str
    amount: float
    category: str


class FixedExpenseCreate(FixedExpenseBase):
    pass


class FixedExpenseUpdate(FixedExpenseBase):
    is_active: Optional[bool] = None


class FixedExpenseResponse(FixedExpenseBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

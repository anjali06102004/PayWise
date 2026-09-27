from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExpenseBase(BaseModel):
    amount: float
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

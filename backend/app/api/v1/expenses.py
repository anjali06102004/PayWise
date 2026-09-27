from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from datetime import datetime
import uuid
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseResponse

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense."""
    expense = Expense(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=expense_data.amount,
        category=expense_data.category,
        subcategory=expense_data.subcategory,
        description=expense_data.description,
        date=expense_data.date or datetime.utcnow()
    )
    
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    return expense


@router.get("/", response_model=List[ExpenseResponse])
async def get_expenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's expenses."""
    result = await db.execute(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.date.desc())
        .limit(limit)
        .offset(offset)
    )
    expenses = result.scalars().all()
    return expenses


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an expense."""
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == current_user.id
        )
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    await db.execute(
        delete(Expense).where(Expense.id == expense_id)
    )
    await db.commit()
    
    return None

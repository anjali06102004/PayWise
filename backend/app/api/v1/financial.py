from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.fixed_expense import FixedExpense
from app.schemas.financial import (
    FinancialProfileCreate,
    FinancialProfileResponse,
    FixedExpenseCreate,
    FixedExpenseResponse
)
from app.services.finance_engine import FinanceEngine

router = APIRouter(prefix="/financial", tags=["financial"])


@router.post("/profile", response_model=FinancialProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_profile(
    profile_data: FinancialProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update financial profile."""
    # Check if profile already exists
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    existing_profile = result.scalar_one_or_none()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Financial profile already exists. Use PUT to update."
        )
    
    profile = FinancialProfile(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        monthly_income=profile_data.monthly_income,
        savings_goal=profile_data.savings_goal,
        currency=profile_data.currency
    )
    
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    
    return profile


@router.get("/profile", response_model=FinancialProfileResponse)
async def get_financial_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's financial profile."""
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found"
        )
    
    return profile


@router.post("/fixed-expenses", response_model=FixedExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_fixed_expense(
    expense_data: FixedExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a fixed expense."""
    expense = FixedExpense(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=expense_data.name,
        amount=expense_data.amount,
        category=expense_data.category
    )
    
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    return expense


@router.get("/fixed-expenses", response_model=List[FixedExpenseResponse])
async def get_fixed_expenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's fixed expenses."""
    result = await db.execute(
        select(FixedExpense)
        .where(FixedExpense.user_id == current_user.id)
        .where(FixedExpense.is_active == True)
    )
    expenses = result.scalars().all()
    return expenses


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard financial state."""
    dashboard_state = await FinanceEngine.calculate_dashboard_state(db, current_user.id)
    
    if "error" in dashboard_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=dashboard_state["error"]
        )
    
    return dashboard_state

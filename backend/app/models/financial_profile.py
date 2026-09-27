from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    monthly_income = Column(Float, nullable=False, default=0.0)
    savings_goal = Column(Float, nullable=False, default=0.0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="financial_profile")

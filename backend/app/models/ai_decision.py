from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision_type = Column(String, nullable=False, index=True)  # purchase_evaluation, risk_assessment, anomaly_detection
    input_context = Column(JSON, nullable=True)
    decision = Column(String, nullable=False)  # ALLOW, CAUTION, REVIEW, low, medium, high
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    model = Column(String, nullable=True)  # jev, rule_based, openai
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="ai_decisions")

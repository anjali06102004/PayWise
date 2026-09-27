from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PurchaseEvaluationRequest(BaseModel):
    amount: float = Field(..., description="Purchase amount")
    category: str = Field(..., description="Purchase category")
    description: Optional[str] = Field(None, description="Purchase description")


class PurchaseEvaluationResponse(BaseModel):
    decision: str  # ALLOW, CAUTION, REVIEW
    confidence: float
    reasoning: str
    remaining_budget: float
    facts: Dict[str, Any]


class RiskAssessmentResponse(BaseModel):
    risk_level: str  # low, medium, high
    confidence: float
    factors: list[str]
    dashboard_summary: Dict[str, Any]


class AnomalyDetectionRequest(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None


class AnomalyDetectionResponse(BaseModel):
    is_anomaly: bool
    anomaly_type: Optional[str]
    confidence: float
    explanation: str

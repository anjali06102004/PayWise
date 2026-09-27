from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ParseExpenseRequest(BaseModel):
    text: str = Field(..., description="Natural language description of expense")


class ParseExpenseResponse(BaseModel):
    amount: float
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    confidence: float


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    tool_results: Optional[Dict[str, Any]] = Field(None, description="Results from tool execution")


class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[str]] = Field(None, description="Tools that should be called")


class InsightResponse(BaseModel):
    insights: List[str]

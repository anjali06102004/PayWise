from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ObservabilityService:
    """Service for AI observability using Langfuse.
    
    Tracks:
    - LLM calls and costs
    - Decision accuracy
    - Token usage
    - Response times
    """
    
    def __init__(self):
        self.enabled = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)
        self.client = None
        
        if self.enabled:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST
                )
                logger.info("Langfuse observability initialized")
            except ImportError:
                logger.warning("Langfuse not installed, observability disabled")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Langfuse: {e}")
                self.enabled = False
    
    def track_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an LLM call."""
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.score(
                name="llm_call",
                value=tokens_used,
                comment=f"Model: {model}, Cost: {cost}"
            )
            logger.info(
                "LLM call tracked",
                extra={
                    "model": model,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    "metadata": metadata
                }
            )
        except Exception as e:
            logger.error(f"Failed to track LLM call: {e}")
    
    def track_decision(
        self,
        decision_type: str,
        decision: str,
        confidence: float,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an AI decision."""
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.score(
                name=f"decision_{decision_type}",
                value=confidence,
                comment=f"Decision: {decision}, Reasoning: {reasoning[:100]}"
            )
            logger.info(
                "Decision tracked",
                extra={
                    "decision_type": decision_type,
                    "decision": decision,
                    "confidence": confidence,
                    "metadata": metadata
                }
            )
        except Exception as e:
            logger.error(f"Failed to track decision: {e}")
    
    def track_expense_parse(
        self,
        input_text: str,
        parsed_amount: float,
        parsed_category: str,
        confidence: float
    ):
        """Track expense parsing accuracy."""
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.score(
                name="expense_parse",
                value=confidence,
                comment=f"Parsed: ₹{parsed_amount} as {parsed_category}"
            )
            logger.info(
                "Expense parse tracked",
                extra={
                    "input_length": len(input_text),
                    "parsed_amount": parsed_amount,
                    "parsed_category": parsed_category,
                    "confidence": confidence
                }
            )
        except Exception as e:
            logger.error(f"Failed to track expense parse: {e}")
    
    def track_chat_interaction(
        self,
        user_message: str,
        ai_response: str,
        tool_calls: Optional[list] = None
    ):
        """Track a chat interaction."""
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.score(
                name="chat_interaction",
                value=len(ai_response),
                comment=f"Tools: {tool_calls}"
            )
            logger.info(
                "Chat interaction tracked",
                extra={
                    "user_message_length": len(user_message),
                    "ai_response_length": len(ai_response),
                    "tool_calls": tool_calls
                }
            )
        except Exception as e:
            logger.error(f"Failed to track chat interaction: {e}")
    
    def flush(self):
        """Flush any pending observations."""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush observations: {e}")


# Global observability instance
observability = ObservabilityService()

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.config import settings
import httpx
import json


class ParsedExpense(BaseModel):
    """Structured output for expense parsing."""
    amount: float = Field(description="The expense amount")
    category: str = Field(description="Expense category (Food, Transport, Shopping, Bills, Entertainment, Health, Education, Subscriptions, Personal, Other)")
    subcategory: Optional[str] = Field(description="More specific subcategory if applicable", default=None)
    description: Optional[str] = Field(description="Brief description of the expense", default=None)
    confidence: float = Field(description="Confidence score from 0 to 1", ge=0, le=1)


class LLMService:
    """Service for LLM interactions with structured output.
    
    This service handles natural language processing tasks:
    - Expense parsing from natural language
    - Spending insights generation
    - Chat responses with tool calling
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.provider = settings.LLM_PROVIDER

    async def parse_expense(self, text: str) -> ParsedExpense:
        """Parse natural language expense text into structured data.
        
        Examples:
        - "₹150 lunch" → amount: 150, category: Food, description: "lunch"
        - "spent 80 on auto" → amount: 80, category: Transport, description: "auto"
        - "I spent 200 on snacks and coffee" → amount: 200, category: Food, description: "snacks and coffee"
        
        Args:
            text: Natural language description of expense
            
        Returns:
            ParsedExpense with structured data
        """
        categories = [
            "Food", "Transport", "Shopping", "Bills", 
            "Entertainment", "Health", "Education", 
            "Subscriptions", "Personal", "Other"
        ]
        
        prompt = f"""Extract expense information from the following text. 
Return ONLY valid JSON with these fields:
- amount: number (the expense amount)
- category: string (must be one of: {', '.join(categories)})
- subcategory: string or null (more specific type, optional)
- description: string or null (brief description)
- confidence: number between 0 and 1

Text: "{text}"

Respond with JSON only, no other text."""

        try:
            if self.provider == "openai":
                return await self._parse_with_openai(prompt)
            else:
                # Fallback to simple rule-based parsing
                return self._parse_with_rules(text)
        except Exception as e:
            # Fallback to rule-based parsing on error
            return self._parse_with_rules(text)

    async def _parse_with_openai(self, prompt: str) -> ParsedExpense:
        """Parse expense using OpenAI API with structured output."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a financial data extractor. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return ParsedExpense(**parsed)

    def _parse_with_rules(self, text: str) -> ParsedExpense:
        """Fallback rule-based parsing for expense extraction."""
        import re
        
        # Extract amount (handles ₹, Rs, or just numbers)
        amount_match = re.search(r'(?:₹|Rs\.?\s*)?(\d+(?:\.\d{1,2})?)', text)
        amount = float(amount_match.group(1)) if amount_match else 0.0
        
        # Simple keyword-based categorization
        text_lower = text.lower()
        
        category_map = {
            'food': ['food', 'lunch', 'dinner', 'breakfast', 'snack', 'coffee', 'tea', 'restaurant', 'cafe', 'meal'],
            'transport': ['auto', 'taxi', 'uber', 'ola', 'bus', 'train', 'metro', 'petrol', 'fuel', 'parking'],
            'shopping': ['shop', 'clothes', 'dress', 'shoes', 'amazon', 'flipkart', 'mall'],
            'bills': ['bill', 'electricity', 'water', 'internet', 'phone', 'recharge'],
            'entertainment': ['movie', 'cinema', 'netflix', 'spotify', 'game', 'concert'],
            'health': ['medicine', 'doctor', 'hospital', 'pharmacy', 'gym', 'fitness'],
            'education': ['book', 'course', 'class', 'tuition', 'exam'],
            'subscriptions': ['subscription', 'membership', 'plan'],
        }
        
        category = "Other"
        for cat, keywords in category_map.items():
            if any(keyword in text_lower for keyword in keywords):
                category = cat.capitalize()
                break
        
        # Extract description (remove amount and common words)
        description = text
        for pattern in [r'(?:₹|Rs\.?\s*)?\d+(?:\.\d{1,2})?', r'spent', r'spend', r'on']:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE)
        description = description.strip()
        
        return ParsedExpense(
            amount=amount,
            category=category,
            description=description if description else None,
            confidence=0.7  # Lower confidence for rule-based parsing
        )

    async def generate_spending_insights(
        self,
        dashboard_data: Dict[str, Any],
        recent_expenses: list
    ) -> list:
        """Generate AI-powered spending insights based on actual data.
        
        Args:
            dashboard_data: Dashboard state from finance engine
            recent_expenses: List of recent expense records
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Insight 1: Largest expense category
        if dashboard_data.get('category_breakdown'):
            categories = dashboard_data['category_breakdown']
            if categories:
                top_category = max(categories.items(), key=lambda x: x[1])
                insights.append(
                    f"💡 {top_category[0]} is currently your largest variable expense "
                    f"this month. You've spent ₹{top_category[1]:.0f} on {top_category[0].lower()}."
                )
        
        # Insight 2: Spending pace
        if dashboard_data.get('spending_velocity') and dashboard_data.get('daily_budget'):
            velocity = dashboard_data['spending_velocity']
            daily_budget = dashboard_data['daily_budget']
            if velocity > daily_budget:
                over = velocity - daily_budget
                insights.append(
                    f"💡 Your current spending pace is ₹{over:.0f}/day above your "
                    f"daily target of ₹{daily_budget:.0f}."
                )
            else:
                under = daily_budget - velocity
                insights.append(
                    f"💡 Your current spending pace is ₹{under:.0f}/day below your "
                    f"daily target of ₹{daily_budget:.0f}. Great job!"
                )
        
        # Insight 3: Budget utilization
        if dashboard_data.get('budget_utilization'):
            utilization = dashboard_data['budget_utilization']
            if utilization > 80:
                insights.append(
                    f"💡 You've used {utilization:.0f}% of your flexible budget. "
                    f"Consider reviewing your spending for the remaining days."
                )
            elif utilization < 30:
                insights.append(
                    f"💡 You've only used {utilization:.0f}% of your flexible budget. "
                    f"You're well within your spending limits."
                )
        
        # Insight 4: Projected balance
        if dashboard_data.get('projected_month_end_balance'):
            projected = dashboard_data['projected_month_end_balance']
            if projected < 0:
                insights.append(
                    f"⚠️ At your current spending pace, you may overspend by "
                    f"₹{abs(projected):.0f} this month."
                )
        
        return insights[:3]  # Return top 3 insights

    async def chat_with_tools(
        self,
        message: str,
        tools: Dict[str, Any],
        tool_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process chat message with tool calling capabilities.
        
        Args:
            message: User's message
            tools: Available tools and their descriptions
            tool_results: Results from tool execution (if tools were called)
            
        Returns:
            AI response
        """
        if tool_results:
            # Generate response based on tool results
            return self._generate_response_from_results(message, tool_results, tools)
        else:
            # Determine if tools are needed
            return await self._determine_tool_needs(message, tools)

    async def _determine_tool_needs(self, message: str, tools: Dict[str, Any]) -> str:
        """Determine which tools to call based on user message."""
        message_lower = message.lower()
        
        # Simple pattern matching for tool selection
        if 'how much' in message_lower and 'spent' in message_lower:
            if 'food' in message_lower:
                return "tool:get_category_expenses:Food"
            elif 'today' in message_lower:
                return "tool:get_today_spending"
            elif 'month' in message_lower:
                return "tool:get_monthly_expenses"
            else:
                return "tool:get_monthly_expenses"
        
        elif 'can i afford' in message_lower or 'can i spend' in message_lower:
            # Extract amount
            import re
            amount_match = re.search(r'(?:₹|Rs\.?\s*)?(\d+(?:\.\d{1,2})?)', message)
            if amount_match:
                amount = amount_match.group(1)
                return f"tool:check_purchase:{amount}"
        
        elif 'where' in message_lower and ('spending' in message_lower or 'spend' in message_lower):
            return "tool:get_category_expenses"
        
        elif 'budget' in message_lower or 'remaining' in message_lower:
            return "tool:get_budget_status"
        
        # Default response
        return "I can help you with your spending questions. Try asking about your expenses, budget, or whether you can afford a purchase."

    def _generate_response_from_results(
        self,
        message: str,
        tool_results: Dict[str, Any],
        tools: Dict[str, Any]
    ) -> str:
        """Generate natural language response from tool results."""
        message_lower = message.lower()
        
        if 'get_category_expenses' in tool_results:
            if 'Food' in message_lower:
                result = tool_results.get('get_category_expenses', {})
                return f"You've spent ₹{result.get('total', 0):.0f} on food this month."
            else:
                result = tool_results.get('get_category_expenses', {})
                categories = result.get('categories', {})
                if categories:
                    top = max(categories.items(), key=lambda x: x[1])
                    return f"You're spending the most on {top[0]}: ₹{top[1]:.0f} this month."
        
        elif 'get_today_spending' in tool_results:
            result = tool_results.get('get_today_spending', {})
            return f"You've spent ₹{result.get('total', 0):.0f} today."
        
        elif 'get_monthly_expenses' in tool_results:
            result = tool_results.get('get_monthly_expenses', {})
            return f"You've spent ₹{result.get('total', 0):.0f} this month."
        
        elif 'check_purchase' in tool_results:
            result = tool_results.get('check_purchase', {})
            decision = result.get('decision', 'REVIEW')
            remaining = result.get('remaining_budget', 0)
            if decision == 'ALLOW':
                return f"Yes, you can afford this purchase. You have ₹{remaining:.0f} remaining in your flexible budget."
            elif decision == 'CAUTION':
                return f"Proceed with caution. This purchase would reduce your remaining budget to ₹{remaining:.0f}."
            else:
                return f"I'd recommend reviewing this purchase. It may impact your budget significantly."
        
        elif 'get_budget_status' in tool_results:
            result = tool_results.get('get_budget_status', {})
            return f"You have ₹{result.get('remaining', 0):.0f} remaining in your flexible budget for this month."
        
        return "I understand your question. Let me help you with that."

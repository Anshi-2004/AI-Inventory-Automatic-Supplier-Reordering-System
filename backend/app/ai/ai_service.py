"""
AI Service: Generates professional supplier emails using LangChain + OpenRouter.

IMPORTANT ARCHITECTURE RULE:
  - All business-critical values (stock levels, quantities, supplier name,
    delivery timeline) are computed by backend business logic and injected
    into the prompt as structured data.
  - The LLM is ONLY responsible for email wording.
  - The LLM does NOT select suppliers, calculate quantities, or make
    procurement decisions.
"""
import json
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmailDraftOutput(BaseModel):
    """Structured output from the LLM — only subject and body."""
    subject: str
    body: str


class InventoryEmailContext(BaseModel):
    """All business-critical values passed to the LLM from backend logic."""
    product_name: str
    product_code: str
    current_stock: float
    unit: str
    average_daily_usage: float
    days_remaining: float
    requested_quantity: float
    supplier_name: str
    supplier_company: str
    required_delivery_days: int
    priority: str
    sender_organization: str = "Inventory Management Team"


EMAIL_PROMPT_TEMPLATE = """You are a professional procurement assistant. 
Write a formal, concise supplier email for a stock replenishment request.

You MUST use ONLY the values provided below. Do NOT invent, change, or estimate any numbers.
Do NOT select a supplier, choose a product, or make any procurement decisions — those have already been made.

--- INVENTORY DATA (use exactly as given) ---
Product Name: {product_name}
Product Code: {product_code}
Current Stock: {current_stock} {unit}
Expected stock duration: approximately {days_remaining} days based on current consumption
Average Daily Usage: {average_daily_usage} {unit}/day
Requested Quantity: {requested_quantity} {unit}
Supplier: {supplier_name} ({supplier_company})
Required Delivery: Within {required_delivery_days} days
Priority: {priority}
Sender: {sender_organization}
---

{format_instructions}

Generate a professional supplier email. The email body should:
1. Greet the supplier by name
2. Clearly state current stock and expected duration
3. Request the exact quantity specified above
4. Specify the required delivery timeframe
5. Ask for delivery confirmation and expected delivery date
6. Sign off professionally from {sender_organization}

Keep the email concise (under 200 words) and professional.
"""


class AIService:
    def __init__(self):
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        self.llm = ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=0.3,  # Lower temp = more consistent, professional output
            max_tokens=800,
        )
        self.parser = PydanticOutputParser(pydantic_object=EmailDraftOutput)

    def _generate_fallback_email(self, context: InventoryEmailContext) -> EmailDraftOutput:
        """Fallback template email generator when LLM API key is unconfigured or returns an error."""
        subject = f"Purchase Order Request: {context.product_name} ({context.product_code}) - Priority: {context.priority}"
        body = (
            f"Dear {context.supplier_name} ({context.supplier_company}),\n\n"
            f"We are writing to request a stock replenishment for {context.product_name} (Code: {context.product_code}).\n\n"
            f"Order & Inventory Details:\n"
            f" - Current Stock: {context.current_stock} {context.unit}\n"
            f" - Estimated Duration: ~{round(context.days_remaining, 1)} days remaining\n"
            f" - Average Daily Usage: {context.average_daily_usage} {context.unit}/day\n"
            f" - Requested Quantity: {context.requested_quantity} {context.unit}\n"
            f" - Required Delivery Timeframe: Within {context.required_delivery_days} days\n"
            f" - Priority Level: {context.priority}\n\n"
            f"Please confirm receipt of this order request and reply with expected delivery confirmation.\n\n"
            f"Best regards,\n"
            f"{context.sender_organization}"
        )
        return EmailDraftOutput(subject=subject, body=body)

    async def generate_supplier_email(self, context: InventoryEmailContext) -> EmailDraftOutput:
        """
        Generate a professional supplier email using LangChain + OpenRouter.
        All values are injected from backend business logic — LLM only writes the prose.
        Falls back to a structured template if OpenRouter is unconfigured or fails.
        """
        key = settings.openrouter_api_key
        if not key or key in ("your-openrouter-api-key-here", "your-api-key-here", "change-me"):
            logger.warning("OpenRouter API key is placeholder or unconfigured. Using template email fallback.")
            return self._generate_fallback_email(context)

        prompt = ChatPromptTemplate.from_template(EMAIL_PROMPT_TEMPLATE)
        chain = prompt | self.llm | self.parser

        try:
            result = await chain.ainvoke({
                "product_name": context.product_name,
                "product_code": context.product_code,
                "current_stock": context.current_stock,
                "unit": context.unit,
                "days_remaining": round(context.days_remaining, 1),
                "average_daily_usage": context.average_daily_usage,
                "requested_quantity": context.requested_quantity,
                "supplier_name": context.supplier_name,
                "supplier_company": context.supplier_company,
                "required_delivery_days": context.required_delivery_days,
                "priority": context.priority,
                "sender_organization": context.sender_organization,
                "format_instructions": self.parser.get_format_instructions(),
            })
            logger.info(
                "AI email generated for product=%s supplier=%s",
                context.product_name, context.supplier_name,
            )
            return result

        except Exception as exc:
            logger.warning("AI email generation failed via OpenRouter (%s). Falling back to template generation.", exc)
            return self._generate_fallback_email(context)


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def reset_ai_service() -> None:
    """Force re-initialization (e.g. after API key change)."""
    global _ai_service
    _ai_service = None

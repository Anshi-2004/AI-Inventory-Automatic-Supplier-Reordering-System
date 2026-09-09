from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.email_log import EmailStatus


class EmailLogResponse(BaseModel):
    id: int
    purchase_order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    recipient_email: str
    subject: str
    body: str
    status: EmailStatus
    generated_by: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailLogListResponse(BaseModel):
    items: list[EmailLogResponse]
    total: int


class EmailApproveRequest(BaseModel):
    """Used when admin edits subject/body before approving."""
    subject: Optional[str] = None
    body: Optional[str] = None


class EmailSendRequest(BaseModel):
    email_log_id: int

from pydantic import BaseModel


class GenerateEmailRequest(BaseModel):
    purchase_order_id: int


class RegenerateEmailRequest(BaseModel):
    email_log_id: int


class EmailDraft(BaseModel):
    subject: str
    body: str


class GenerateEmailResponse(BaseModel):
    email_log_id: int
    purchase_order_id: int
    subject: str
    body: str
    recipient_email: str
    status: str

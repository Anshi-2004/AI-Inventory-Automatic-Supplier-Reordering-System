from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.alert import AlertSeverity, AlertStatus, AlertType


class AlertResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    alert_type: AlertType
    current_stock: float
    daily_usage: float
    days_remaining: Optional[float] = None
    threshold: Optional[float] = None
    severity: AlertSeverity
    message: str
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int

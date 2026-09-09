from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.inventory_transaction import TransactionType


class TransactionCreate(BaseModel):
    product_id: int
    transaction_type: TransactionType
    quantity: float
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    batch_id: Optional[int] = None
    transaction_date: Optional[datetime] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Transaction quantity must be positive")
        return v


class BatchCreate(BaseModel):
    product_id: int
    batch_number: str
    quantity: float
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    received_date: date

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Batch quantity must be positive")
        return v


class TransactionResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: TransactionType
    quantity: float
    stock_after: Optional[float] = None
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    transaction_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchResponse(BaseModel):
    id: int
    product_id: int
    batch_number: str
    quantity: float
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    received_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryStatusItem(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    category: str
    current_quantity: float
    unit: str
    average_daily_usage: float
    days_remaining: Optional[float]
    status: str
    primary_supplier_name: Optional[str] = None
    alert_days: int
    critical_days: int
    emergency_reserve: float

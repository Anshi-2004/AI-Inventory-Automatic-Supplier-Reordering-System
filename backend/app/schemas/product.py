from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.product import ProductStatus


class ProductCreate(BaseModel):
    product_name: str
    product_code: str
    category: str
    description: Optional[str] = None
    current_quantity: float = 0.0
    unit: str = "units"
    minimum_stock: float = 0.0
    average_daily_usage: float = 0.0
    alert_days: int = 7
    critical_days: int = 3
    emergency_reserve: float = 0.0
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = None
    primary_supplier_id: Optional[int] = None

    @field_validator("current_quantity", "minimum_stock", "emergency_reserve")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("average_daily_usage")
    @classmethod
    def non_negative_usage(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Average daily usage cannot be negative")
        return v


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    minimum_stock: Optional[float] = None
    average_daily_usage: Optional[float] = None
    alert_days: Optional[int] = None
    critical_days: Optional[int] = None
    emergency_reserve: Optional[float] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = None
    primary_supplier_id: Optional[int] = None
    status: Optional[ProductStatus] = None


class SupplierProductInfo(BaseModel):
    supplier_id: int
    supplier_name: str
    company_name: str
    unit_price: Optional[float] = None
    minimum_order_quantity: float
    delivery_days: int
    priority: int
    emergency_available: bool

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    product_name: str
    product_code: str
    category: str
    description: Optional[str] = None
    current_quantity: float
    unit: str
    minimum_stock: float
    average_daily_usage: float
    alert_days: int
    critical_days: int
    emergency_reserve: float
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = None
    primary_supplier_id: Optional[int] = None
    status: ProductStatus
    days_remaining: Optional[float] = None
    recommended_reorder_qty: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int

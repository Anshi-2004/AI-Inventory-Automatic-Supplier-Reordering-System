from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.supplier import SupplierPriority, SupplierStatus


class SupplierCreate(BaseModel):
    supplier_name: str
    company_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: str = "email"
    average_delivery_days: int = 7
    emergency_available: bool = False
    priority: SupplierPriority = SupplierPriority.MEDIUM


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    average_delivery_days: Optional[int] = None
    emergency_available: Optional[bool] = None
    priority: Optional[SupplierPriority] = None
    status: Optional[SupplierStatus] = None


class SupplierProductLink(BaseModel):
    """Link a supplier to a product with pricing/delivery info."""
    product_id: int
    unit_price: Optional[float] = None
    minimum_order_quantity: float = 1.0
    delivery_days: int = 7
    priority: int = 1
    emergency_available: bool = False


class SupplierResponse(BaseModel):
    id: int
    supplier_name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: str
    average_delivery_days: int
    emergency_available: bool
    priority: SupplierPriority
    status: SupplierStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    items: list[SupplierResponse]
    total: int

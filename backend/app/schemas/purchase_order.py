from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.purchase_order import OrderPriority, PurchaseOrderStatus


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    requested_quantity: float
    unit_price: Optional[float] = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    required_by_date: Optional[datetime] = None
    priority: OrderPriority = OrderPriority.NORMAL
    notes: Optional[str] = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderReceiveItem(BaseModel):
    item_id: int
    received_quantity: float


class PurchaseOrderReceive(BaseModel):
    items: list[PurchaseOrderReceiveItem]


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    requested_quantity: float
    received_quantity: float = 0.0
    unit_price: Optional[float] = None

    model_config = {"from_attributes": True}


class PurchaseOrderResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    order_date: datetime
    required_by_date: Optional[datetime] = None
    status: PurchaseOrderStatus
    priority: OrderPriority
    total_items: int
    notes: Optional[str] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    items: list[PurchaseOrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    items: list[PurchaseOrderResponse]
    total: int

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.models.user import User
from app.repositories.purchase_order_repo import PurchaseOrderRepository
from app.schemas.purchase_order import (
    PurchaseOrderCreate, PurchaseOrderListResponse,
    PurchaseOrderReceive, PurchaseOrderResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Purchase Orders"])


def _enrich_order(order) -> dict:
    items = []
    if order.items:
        for item in order.items:
            product = item.product
            items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.product_name if product else None,
                "product_code": product.product_code if product else None,
                "requested_quantity": item.requested_quantity,
                "received_quantity": item.received_quantity,
                "unit_price": item.unit_price,
            })
    return {
        "id": order.id,
        "supplier_id": order.supplier_id,
        "supplier_name": order.supplier.supplier_name if order.supplier else None,
        "order_date": order.order_date,
        "required_by_date": order.required_by_date,
        "status": order.status,
        "priority": order.priority,
        "total_items": order.total_items,
        "notes": order.notes,
        "created_by": order.created_by,
        "approved_by": order.approved_by,
        "approved_at": order.approved_at,
        "items": items,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.post("", response_model=PurchaseOrderResponse, status_code=201,
             summary="Create a purchase order")
async def create_order(
    data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.create_order(data, created_by=current_user.id)
    return _enrich_order(order)


@router.get("", response_model=PurchaseOrderListResponse, summary="List all purchase orders")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = PurchaseOrderRepository(db)
    items, total = await repo.get_all(skip=skip, limit=limit)
    return PurchaseOrderListResponse(items=[_enrich_order(o) for o in items], total=total)


@router.get("/{order_id}", response_model=PurchaseOrderResponse, summary="Get order by ID")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = PurchaseOrderRepository(db)
    order = await repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return _enrich_order(order)


@router.post("/{order_id}/approve", response_model=PurchaseOrderResponse,
             summary="Approve a purchase order (Admin)")
async def approve_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = OrderService(db)
    order = await service.approve_order(order_id, approved_by=admin.id)
    repo = PurchaseOrderRepository(db)
    order = await repo.get_by_id(order.id)
    return _enrich_order(order)


@router.post("/{order_id}/cancel", response_model=PurchaseOrderResponse,
             summary="Cancel a purchase order")
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.cancel_order(order_id)
    repo = PurchaseOrderRepository(db)
    order = await repo.get_by_id(order.id)
    return _enrich_order(order)


@router.post("/{order_id}/receive", response_model=PurchaseOrderResponse,
             summary="Mark order items as received")
async def receive_order(
    order_id: int,
    data: PurchaseOrderReceive,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.receive_order(order_id, data, received_by=current_user.id)
    repo = PurchaseOrderRepository(db)
    order = await repo.get_by_id(order.id)
    return _enrich_order(order)

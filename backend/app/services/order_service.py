"""
Purchase order service: orchestrates order creation and lifecycle.
Includes duplicate prevention and supplier selection.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.purchase_order import OrderPriority, PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.purchase_order_repo import PurchaseOrderRepository
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderReceive
from app.services.inventory_service import calculate_days_remaining
from app.services.reorder_calc_service import calculate_reorder_quantity
from app.services.supplier_selection_service import determine_order_priority

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = PurchaseOrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.inv_repo = InventoryRepository(db)

    async def create_order(self, data: PurchaseOrderCreate, created_by: int) -> PurchaseOrder:
        """Create a new purchase order with duplicate prevention."""
        # Verify supplier exists
        supplier = await self.supplier_repo.get_by_id(data.supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")

        # Duplicate prevention: check each product
        for item_data in data.items:
            if await self.order_repo.has_active_order_for_product(item_data.product_id):
                product = await self.product_repo.get_by_id(item_data.product_id)
                name = product.product_name if product else str(item_data.product_id)
                raise HTTPException(
                    status_code=409,
                    detail=f"An active purchase order already exists for product '{name}'. "
                           "Resolve or cancel it before creating a new one.",
                )

        order = PurchaseOrder(
            supplier_id=data.supplier_id,
            required_by_date=data.required_by_date,
            status=PurchaseOrderStatus.PENDING_APPROVAL,
            priority=data.priority,
            total_items=len(data.items),
            notes=data.notes,
            created_by=created_by,
        )
        order = await self.order_repo.create(order)

        for item_data in data.items:
            product = await self.product_repo.get_by_id(item_data.product_id)
            if not product:
                raise HTTPException(
                    status_code=404, detail=f"Product {item_data.product_id} not found"
                )
            item = PurchaseOrderItem(
                purchase_order_id=order.id,
                product_id=item_data.product_id,
                requested_quantity=item_data.requested_quantity,
                unit_price=item_data.unit_price,
            )
            self.db.add(item)

        await self.db.flush()
        logger.info(
            "Created purchase order id=%s for supplier=%s with %d items",
            order.id, supplier.supplier_name, len(data.items),
        )
        return await self.order_repo.get_by_id(order.id)

    async def approve_order(self, order_id: int, approved_by: int) -> PurchaseOrder:
        order = await self._get_order_or_404(order_id)
        if order.status not in (PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.DRAFT):
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be approved from status '{order.status.value}'",
            )
        order.status = PurchaseOrderStatus.APPROVED
        order.approved_by = approved_by
        order.approved_at = datetime.now(timezone.utc)
        return await self.order_repo.update(order)

    async def cancel_order(self, order_id: int) -> PurchaseOrder:
        order = await self._get_order_or_404(order_id)
        if order.status in (PurchaseOrderStatus.DELIVERED, PurchaseOrderStatus.CANCELLED):
            raise HTTPException(status_code=400, detail="Order cannot be cancelled")
        order.status = PurchaseOrderStatus.CANCELLED
        return await self.order_repo.update(order)

    async def receive_order(
        self, order_id: int, data: PurchaseOrderReceive, received_by: int
    ) -> PurchaseOrder:
        """
        Mark order items as received, create IN inventory transactions,
        update product stock, and mark order DELIVERED.
        """
        order = await self._get_order_or_404(order_id)
        if order.status not in (
            PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.DISPATCHED,
            PurchaseOrderStatus.EMAIL_SENT, PurchaseOrderStatus.APPROVED,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot receive order from status '{order.status.value}'",
            )

        item_map = {item.id: item for item in order.items}

        for recv in data.items:
            item = item_map.get(recv.item_id)
            if not item:
                raise HTTPException(
                    status_code=404, detail=f"Order item {recv.item_id} not found"
                )
            if recv.received_quantity <= 0:
                raise HTTPException(
                    status_code=400, detail="Received quantity must be positive"
                )
            item.received_quantity = recv.received_quantity

            # Update product stock
            product = await self.product_repo.get_by_id(item.product_id)
            if product:
                product.current_quantity += recv.received_quantity
                txn = InventoryTransaction(
                    product_id=product.id,
                    transaction_type=TransactionType.IN,
                    quantity=recv.received_quantity,
                    stock_after=product.current_quantity,
                    reason=f"Received from purchase order #{order_id}",
                    reference_id=str(order_id),
                    created_by=received_by,
                )
                await self.inv_repo.create_transaction(txn)
                logger.info(
                    "Received %.2f units of %s from PO #%s. New stock: %.2f",
                    recv.received_quantity, product.product_name, order_id, product.current_quantity,
                )

        order.status = PurchaseOrderStatus.DELIVERED
        return await self.order_repo.update(order)

    async def _get_order_or_404(self, order_id: int) -> PurchaseOrder:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        return order

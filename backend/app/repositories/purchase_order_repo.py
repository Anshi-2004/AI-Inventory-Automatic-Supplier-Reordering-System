from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, order: PurchaseOrder) -> PurchaseOrder:
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
                selectinload(PurchaseOrder.supplier),
            )
            .where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[PurchaseOrder], int]:
        count_r = await self.db.execute(select(func.count()).select_from(PurchaseOrder))
        total = count_r.scalar_one()
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
                selectinload(PurchaseOrder.supplier),
            )
            .order_by(PurchaseOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def has_active_order_for_product(self, product_id: int) -> bool:
        """
        Duplicate prevention: check if any non-cancelled/non-delivered order
        already contains this product.
        """
        active_statuses = [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.PENDING_APPROVAL,
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.EMAIL_GENERATED,
            PurchaseOrderStatus.EMAIL_SENT,
            PurchaseOrderStatus.CONFIRMED,
            PurchaseOrderStatus.DISPATCHED,
        ]
        result = await self.db.execute(
            select(PurchaseOrderItem)
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(
                and_(
                    PurchaseOrderItem.product_id == product_id,
                    PurchaseOrder.status.in_(active_statuses),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def update(self, order: PurchaseOrder) -> PurchaseOrder:
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_pending(self) -> list[PurchaseOrder]:
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.supplier))
            .where(
                PurchaseOrder.status.in_([
                    PurchaseOrderStatus.PENDING_APPROVAL,
                    PurchaseOrderStatus.APPROVED,
                    PurchaseOrderStatus.EMAIL_GENERATED,
                ])
            )
        )
        return list(result.scalars().all())

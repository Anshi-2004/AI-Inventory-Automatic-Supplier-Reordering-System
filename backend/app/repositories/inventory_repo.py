from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory_transaction import InventoryTransaction
from app.models.product_batch import ProductBatch


class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transaction(self, txn: InventoryTransaction) -> InventoryTransaction:
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def get_transactions_for_product(
        self, product_id: int, skip: int = 0, limit: int = 50
    ) -> list[InventoryTransaction]:
        result = await self.db.execute(
            select(InventoryTransaction)
            .where(InventoryTransaction.product_id == product_id)
            .order_by(desc(InventoryTransaction.transaction_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Batch (FEFO) ─────────────────────────────────────────────────────────
    async def create_batch(self, batch: ProductBatch) -> ProductBatch:
        self.db.add(batch)
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def get_batches_for_product_fefo(self, product_id: int) -> list[ProductBatch]:
        """Return batches ordered by expiry_date ASC (FEFO: earliest expiry first)."""
        result = await self.db.execute(
            select(ProductBatch)
            .where(
                ProductBatch.product_id == product_id,
                ProductBatch.quantity > 0,
            )
            .order_by(ProductBatch.expiry_date.asc().nulls_last())
        )
        return list(result.scalars().all())

    async def get_all_batches_expiring_within(self, days: int) -> list[ProductBatch]:
        from datetime import date, timedelta
        cutoff = date.today() + timedelta(days=days)
        today = date.today()
        result = await self.db.execute(
            select(ProductBatch)
            .where(
                ProductBatch.expiry_date <= cutoff,
                ProductBatch.expiry_date >= today,
                ProductBatch.quantity > 0,
            )
            .order_by(ProductBatch.expiry_date)
        )
        return list(result.scalars().all())

    async def get_expired_batches(self) -> list[ProductBatch]:
        from datetime import date
        result = await self.db.execute(
            select(ProductBatch)
            .where(
                ProductBatch.expiry_date < date.today(),
                ProductBatch.quantity > 0,
            )
        )
        return list(result.scalars().all())

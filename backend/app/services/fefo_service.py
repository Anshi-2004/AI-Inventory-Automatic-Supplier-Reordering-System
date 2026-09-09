"""
FEFO (First Expire, First Out) batch consumption logic.
When stock is consumed (OUT transaction), batches with the earliest
expiry date are depleted first.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product import Product
from app.repositories.inventory_repo import InventoryRepository

logger = logging.getLogger(__name__)


class FEFOService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InventoryRepository(db)

    async def consume_stock(
        self,
        product: Product,
        quantity: float,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> list[InventoryTransaction]:
        """
        Consume `quantity` units from product using FEFO batch ordering.
        Creates one InventoryTransaction per batch depleted.
        Updates product.current_quantity.
        Returns list of created transactions.
        """
        if quantity <= 0:
            raise ValueError("Consume quantity must be positive")
        if product.current_quantity < quantity:
            raise ValueError(
                f"Insufficient stock: available={product.current_quantity}, requested={quantity}"
            )

        batches = await self.repo.get_batches_for_product_fefo(product.id)
        remaining = quantity
        transactions = []

        for batch in batches:
            if remaining <= 0:
                break

            consume_from_batch = min(batch.quantity, remaining)
            batch.quantity -= consume_from_batch
            remaining -= consume_from_batch

            product.current_quantity -= consume_from_batch
            txn = InventoryTransaction(
                product_id=product.id,
                transaction_type=TransactionType.OUT,
                quantity=consume_from_batch,
                stock_after=product.current_quantity,
                reason=reason,
                reference_id=reference_id,
                batch_id=batch.id,
                transaction_date=datetime.now(timezone.utc),
                created_by=created_by,
            )
            txn = await self.repo.create_transaction(txn)
            transactions.append(txn)
            logger.debug(
                "FEFO: consumed %.2f from batch %s (product_id=%s). "
                "Batch remaining=%.2f, product remaining=%.2f",
                consume_from_batch, batch.batch_number, product.id,
                batch.quantity, product.current_quantity,
            )

        # If batches don't cover the full quantity, do a simple OUT for the remainder
        if remaining > 0:
            product.current_quantity -= remaining
            txn = InventoryTransaction(
                product_id=product.id,
                transaction_type=TransactionType.OUT,
                quantity=remaining,
                stock_after=product.current_quantity,
                reason=reason,
                reference_id=reference_id,
                transaction_date=datetime.now(timezone.utc),
                created_by=created_by,
            )
            txn = await self.repo.create_transaction(txn)
            transactions.append(txn)

        return transactions

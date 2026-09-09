from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier import Supplier, SupplierStatus
from app.models.supplier_product import SupplierProduct


class SupplierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        result = await self.db.execute(
            select(Supplier)
            .options(selectinload(Supplier.supplier_products))
            .where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Supplier]:
        result = await self.db.execute(select(Supplier).where(Supplier.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Supplier], int]:
        all_result = await self.db.execute(select(Supplier))
        total = len(list(all_result.scalars().all()))
        result = await self.db.execute(
            select(Supplier).order_by(Supplier.supplier_name).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_active(self) -> list[Supplier]:
        result = await self.db.execute(
            select(Supplier).where(Supplier.status == SupplierStatus.ACTIVE)
        )
        return list(result.scalars().all())

    async def create(self, supplier: Supplier) -> Supplier:
        self.db.add(supplier)
        await self.db.flush()
        await self.db.refresh(supplier)
        return supplier

    async def update(self, supplier: Supplier) -> Supplier:
        await self.db.flush()
        await self.db.refresh(supplier)
        return supplier

    async def delete(self, supplier: Supplier) -> None:
        await self.db.delete(supplier)
        await self.db.flush()

    async def get_supplier_products_for_product(self, product_id: int) -> list[SupplierProduct]:
        result = await self.db.execute(
            select(SupplierProduct)
            .options(selectinload(SupplierProduct.supplier))
            .where(SupplierProduct.product_id == product_id)
            .order_by(SupplierProduct.priority)
        )
        return list(result.scalars().all())

    async def get_supplier_product(self, supplier_id: int, product_id: int) -> Optional[SupplierProduct]:
        result = await self.db.execute(
            select(SupplierProduct)
            .where(SupplierProduct.supplier_id == supplier_id, SupplierProduct.product_id == product_id)
        )
        return result.scalar_one_or_none()

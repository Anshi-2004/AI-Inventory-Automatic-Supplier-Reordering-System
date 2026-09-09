from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductStatus
from app.models.supplier_product import SupplierProduct


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.primary_supplier), selectinload(Product.supplier_products))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.product_code == code))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Product], int]:
        count_r = await self.db.execute(select(func.count()).select_from(Product))
        total = count_r.scalar_one()
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.primary_supplier))
            .order_by(Product.product_name)
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_active(self) -> list[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.primary_supplier), selectinload(Product.supplier_products))
            .where(Product.status != ProductStatus.EXPIRED)
            .order_by(Product.product_name)
        )
        return list(result.scalars().all())

    async def create(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product) -> Product:
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.flush()

    async def get_by_status(self, status: ProductStatus) -> list[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.primary_supplier))
            .where(Product.status == status)
        )
        return list(result.scalars().all())

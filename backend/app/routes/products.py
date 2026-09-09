from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.models.product import Product, ProductStatus
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.repositories.product_repo import ProductRepository
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services.inventory_service import calculate_days_remaining
from app.services.reorder_calc_service import calculate_reorder_quantity

router = APIRouter(prefix="/products", tags=["Products"])


def _enrich_product(product: Product) -> dict:
    days = calculate_days_remaining(product)
    data = {
        "id": product.id,
        "product_name": product.product_name,
        "product_code": product.product_code,
        "category": product.category,
        "description": product.description,
        "current_quantity": product.current_quantity,
        "unit": product.unit,
        "minimum_stock": product.minimum_stock,
        "average_daily_usage": product.average_daily_usage,
        "alert_days": product.alert_days,
        "critical_days": product.critical_days,
        "emergency_reserve": product.emergency_reserve,
        "expiry_date": product.expiry_date,
        "storage_location": product.storage_location,
        "primary_supplier_id": product.primary_supplier_id,
        "status": product.status,
        "days_remaining": round(days, 2) if days is not None else None,
        "recommended_reorder_qty": None,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
    return data


@router.post("", response_model=ProductResponse, status_code=201,
             summary="Create a new product")
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    existing = await repo.get_by_code(data.product_code)
    if existing:
        raise HTTPException(status_code=409, detail="Product code already exists")

    product = Product(**data.model_dump())
    product = await repo.create(product)
    return _enrich_product(product)


@router.get("", response_model=ProductListResponse, summary="List all products")
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    items, total = await repo.get_all(skip=skip, limit=limit)
    return ProductListResponse(items=[_enrich_product(p) for p in items], total=total)


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product by ID")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _enrich_product(product)


@router.put("/{product_id}", response_model=ProductResponse, summary="Update a product")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    product = await repo.update(product)
    return _enrich_product(product)


@router.delete("/{product_id}", status_code=204, summary="Delete a product (Admin only)")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await repo.delete(product)

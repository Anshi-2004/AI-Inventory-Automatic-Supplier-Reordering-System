from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.models.user import User
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.supplier import (
    SupplierCreate, SupplierListResponse, SupplierProductLink,
    SupplierResponse, SupplierUpdate,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("", response_model=SupplierResponse, status_code=201, summary="Create a supplier")
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SupplierRepository(db)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Supplier email already exists")
    supplier = Supplier(**data.model_dump())
    return await repo.create(supplier)


@router.get("", response_model=SupplierListResponse, summary="List all suppliers")
async def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SupplierRepository(db)
    items, total = await repo.get_all(skip=skip, limit=limit)
    return SupplierListResponse(items=items, total=total)


@router.get("/{supplier_id}", response_model=SupplierResponse, summary="Get supplier by ID")
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse, summary="Update a supplier")
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    return await repo.update(supplier)


@router.delete("/{supplier_id}", status_code=204, summary="Delete a supplier (Admin only)")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    await repo.delete(supplier)


@router.post("/{supplier_id}/products", status_code=201, summary="Link a product to a supplier")
async def link_product(
    supplier_id: int,
    data: SupplierProductLink,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    existing = await repo.get_supplier_product(supplier_id, data.product_id)
    if existing:
        raise HTTPException(status_code=409, detail="Supplier-product link already exists")

    sp = SupplierProduct(
        supplier_id=supplier_id,
        product_id=data.product_id,
        unit_price=data.unit_price,
        minimum_order_quantity=data.minimum_order_quantity,
        delivery_days=data.delivery_days,
        priority=data.priority,
        emergency_available=data.emergency_available,
    )
    db.add(sp)
    await db.flush()
    return {"message": "Product linked to supplier", "supplier_product_id": sp.id}

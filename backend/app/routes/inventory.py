from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product_batch import ProductBatch
from app.models.user import User
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.inventory import (
    BatchCreate, BatchResponse, InventoryStatusItem,
    TransactionCreate, TransactionResponse,
)
from app.services.fefo_service import FEFOService
from app.services.inventory_monitor_service import run_inventory_check
from app.services.inventory_service import calculate_days_remaining, determine_product_status

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/transactions", response_model=TransactionResponse, status_code=201,
             summary="Record a stock movement")
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product_repo = ProductRepository(db)
    inv_repo = InventoryRepository(db)
    product = await product_repo.get_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.transaction_type == TransactionType.OUT:
        # Use FEFO for stock consumption
        if product.current_quantity < data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock: available={product.current_quantity}, requested={data.quantity}",
            )
        fefo = FEFOService(db)
        txns = await fefo.consume_stock(
            product=product,
            quantity=data.quantity,
            reason=data.reason,
            reference_id=data.reference_id,
            created_by=current_user.id,
        )
        # Update product status
        product.status = determine_product_status(product)
        if not txns:
            raise HTTPException(status_code=500, detail="Stock consume returned no transactions")
        return txns[0]

    elif data.transaction_type == TransactionType.IN:
        product.current_quantity += data.quantity
        txn = InventoryTransaction(
            product_id=product.id,
            transaction_type=TransactionType.IN,
            quantity=data.quantity,
            stock_after=product.current_quantity,
            reason=data.reason,
            reference_id=data.reference_id,
            batch_id=data.batch_id,
            transaction_date=data.transaction_date or datetime.now(timezone.utc),
            created_by=current_user.id,
        )
        txn = await inv_repo.create_transaction(txn)
        product.status = determine_product_status(product)
        return txn

    elif data.transaction_type == TransactionType.ADJUSTMENT:
        old_qty = product.current_quantity
        product.current_quantity = data.quantity  # ADJUSTMENT sets absolute quantity
        txn = InventoryTransaction(
            product_id=product.id,
            transaction_type=TransactionType.ADJUSTMENT,
            quantity=data.quantity - old_qty,  # delta
            stock_after=product.current_quantity,
            reason=data.reason or "Manual adjustment",
            reference_id=data.reference_id,
            transaction_date=data.transaction_date or datetime.now(timezone.utc),
            created_by=current_user.id,
        )
        txn = await inv_repo.create_transaction(txn)
        product.status = determine_product_status(product)
        return txn

    else:
        # DAMAGE, EXPIRED, RETURN
        if data.transaction_type in (TransactionType.DAMAGE, TransactionType.EXPIRED):
            if product.current_quantity < data.quantity:
                raise HTTPException(status_code=400, detail="Cannot remove more than current stock")
            product.current_quantity -= data.quantity
        else:  # RETURN
            product.current_quantity += data.quantity

        txn = InventoryTransaction(
            product_id=product.id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            stock_after=product.current_quantity,
            reason=data.reason,
            reference_id=data.reference_id,
            transaction_date=data.transaction_date or datetime.now(timezone.utc),
            created_by=current_user.id,
        )
        txn = await inv_repo.create_transaction(txn)
        product.status = determine_product_status(product)
        return txn


@router.post("/batches", response_model=BatchResponse, status_code=201,
             summary="Register a new product batch")
async def create_batch(
    data: BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product_repo = ProductRepository(db)
    inv_repo = InventoryRepository(db)
    product = await product_repo.get_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    batch = ProductBatch(**data.model_dump())
    batch = await inv_repo.create_batch(batch)
    return batch


@router.get("/status", response_model=list[InventoryStatusItem], summary="Get full inventory status")
async def get_inventory_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    products, _ = await repo.get_all(limit=1000)
    result = []
    for p in products:
        days = calculate_days_remaining(p)
        supplier_name = p.primary_supplier.supplier_name if p.primary_supplier else None
        result.append(InventoryStatusItem(
            product_id=p.id,
            product_name=p.product_name,
            product_code=p.product_code,
            category=p.category,
            current_quantity=p.current_quantity,
            unit=p.unit,
            average_daily_usage=p.average_daily_usage,
            days_remaining=round(days, 2) if days is not None else None,
            status=p.status.value,
            primary_supplier_name=supplier_name,
            alert_days=p.alert_days,
            critical_days=p.critical_days,
            emergency_reserve=p.emergency_reserve,
        ))
    return result


@router.get("/low-stock", response_model=list[InventoryStatusItem], summary="Products in low stock")
async def get_low_stock(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.product import ProductStatus
    repo = ProductRepository(db)
    products = await repo.get_by_status(ProductStatus.LOW_STOCK)
    days_items = []
    for p in products:
        days = calculate_days_remaining(p)
        supplier_name = p.primary_supplier.supplier_name if p.primary_supplier else None
        days_items.append(InventoryStatusItem(
            product_id=p.id, product_name=p.product_name, product_code=p.product_code,
            category=p.category, current_quantity=p.current_quantity, unit=p.unit,
            average_daily_usage=p.average_daily_usage,
            days_remaining=round(days, 2) if days is not None else None,
            status=p.status.value, primary_supplier_name=supplier_name,
            alert_days=p.alert_days, critical_days=p.critical_days,
            emergency_reserve=p.emergency_reserve,
        ))
    return days_items


@router.get("/critical", response_model=list[InventoryStatusItem], summary="Products in critical stock")
async def get_critical(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.product import ProductStatus
    repo = ProductRepository(db)
    products = await repo.get_by_status(ProductStatus.CRITICAL)
    result = []
    for p in products:
        days = calculate_days_remaining(p)
        supplier_name = p.primary_supplier.supplier_name if p.primary_supplier else None
        result.append(InventoryStatusItem(
            product_id=p.id, product_name=p.product_name, product_code=p.product_code,
            category=p.category, current_quantity=p.current_quantity, unit=p.unit,
            average_daily_usage=p.average_daily_usage,
            days_remaining=round(days, 2) if days is not None else None,
            status=p.status.value, primary_supplier_name=supplier_name,
            alert_days=p.alert_days, critical_days=p.critical_days,
            emergency_reserve=p.emergency_reserve,
        ))
    return result


@router.get("/history/{product_id}", response_model=list[TransactionResponse],
            summary="Get transaction history for a product")
async def get_history(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product_repo = ProductRepository(db)
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    inv_repo = InventoryRepository(db)
    return await inv_repo.get_transactions_for_product(product_id, skip=skip, limit=limit)


@router.post("/check", summary="Manually trigger inventory check (Admin)")
async def manual_inventory_check(current_user: User = Depends(get_current_user)):
    """Manually trigger the inventory check (same logic as scheduler)."""
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    summary = await run_inventory_check()
    return {"message": "Inventory check complete", "summary": summary}

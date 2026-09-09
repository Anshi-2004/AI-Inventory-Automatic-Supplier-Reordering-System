"""
Inventory Monitor Service: orchestrates the full daily inventory check.
Called by the APScheduler job. Separated from scheduler for testability.

Flow:
  1. Fetch active products
  2. Calculate days remaining
  3. Check low/critical/emergency stock → create alerts (dedup)
  4. Check expiry
  5. Check supplier lead time risk
  6. For products needing orders: select supplier, calc qty, create PO (dedup)
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.purchase_order import OrderPriority, PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.repositories.product_repo import ProductRepository
from app.repositories.purchase_order_repo import PurchaseOrderRepository
from app.repositories.supplier_repo import SupplierRepository
from app.services.alert_service import AlertService
from app.services.expiry_service import ExpiryService
from app.services.inventory_service import (
    calculate_days_remaining,
    determine_product_status,
    is_emergency_stock,
    is_lead_time_risk,
)
from app.services.reorder_calc_service import calculate_reorder_quantity
from app.services.supplier_selection_service import (
    determine_order_priority,
    select_best_supplier,
)

logger = logging.getLogger(__name__)


async def run_inventory_check() -> dict:
    """
    Run a full inventory check across all active products.
    Creates a new DB session (used by APScheduler which runs outside request context).
    Returns summary dict.
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await _check_inventory(db)
            await db.commit()
            return result
        except Exception as exc:
            await db.rollback()
            logger.error("Inventory check failed: %s", exc, exc_info=True)
            raise


async def _check_inventory(db: AsyncSession) -> dict:
    product_repo = ProductRepository(db)
    supplier_repo = SupplierRepository(db)
    order_repo = PurchaseOrderRepository(db)
    alert_service = AlertService(db)
    expiry_service = ExpiryService(db)

    products = await product_repo.get_active()
    logger.info("Inventory check started. Checking %d products.", len(products))

    summary = {
        "products_checked": len(products),
        "alerts_created": 0,
        "orders_created": 0,
        "errors": [],
    }

    for product in products:
        try:
            # ── Update product status ────────────────────────────────────────
            new_status = determine_product_status(product)
            product.status = new_status

            # ── Expiry alerts ────────────────────────────────────────────────
            expiry_alerts = await expiry_service.check_product_expiry(product)
            summary["alerts_created"] += len(expiry_alerts)

            # ── Stock alerts ─────────────────────────────────────────────────
            stock_alerts = await alert_service.check_and_create_alerts(product)
            summary["alerts_created"] += len(stock_alerts)

            # ── Determine if a purchase order is needed ──────────────────────
            days_remaining = calculate_days_remaining(product)
            needs_order = (
                days_remaining is not None
                and (days_remaining <= product.alert_days or is_emergency_stock(product))
                and product.current_quantity > 0  # skip completely expired
            )

            if not needs_order:
                continue

            # ── Check for existing active order (duplicate prevention) ────────
            if await order_repo.has_active_order_for_product(product.id):
                logger.debug(
                    "Skipping PO creation for %s: active order exists.", product.product_name
                )
                continue

            # ── Supplier selection ────────────────────────────────────────────
            sp_list = await supplier_repo.get_supplier_products_for_product(product.id)
            is_emergency = is_emergency_stock(product)
            selected_sp = select_best_supplier(sp_list, is_emergency=is_emergency)

            if not selected_sp:
                # Fallback: use primary supplier
                if product.primary_supplier_id:
                    from app.models.supplier_product import SupplierProduct
                    # Create a virtual SupplierProduct with supplier defaults
                    supplier = await supplier_repo.get_by_id(product.primary_supplier_id)
                    if not supplier:
                        logger.warning("No supplier found for %s", product.product_name)
                        continue
                    # Use a minimal SupplierProduct-like object
                    class _MinimalSP:
                        delivery_days = supplier.average_delivery_days or 7
                        minimum_order_quantity = 1.0
                        unit_price = None
                        emergency_available = supplier.emergency_available
                        priority = 1
                    selected_sp = _MinimalSP()
                    selected_sp.supplier = supplier
                    selected_sp.supplier_id = supplier.id
                    selected_sp.product_id = product.id
                else:
                    logger.warning(
                        "No suitable supplier found for %s. Cannot create PO.", product.product_name
                    )
                    continue

            # ── Lead time risk check ──────────────────────────────────────────
            if is_lead_time_risk(product, selected_sp.delivery_days):
                logger.warning(
                    "LEAD TIME RISK: %s may run out before supplier can deliver "
                    "(days_remaining=%.1f, delivery=%d days).",
                    product.product_name, days_remaining or 0, selected_sp.delivery_days,
                )

            # ── Reorder quantity ──────────────────────────────────────────────
            reorder_qty = calculate_reorder_quantity(product, selected_sp)

            # ── Create purchase order ─────────────────────────────────────────
            priority = determine_order_priority(days_remaining, is_emergency)
            required_by = datetime.now(timezone.utc) + timedelta(days=selected_sp.delivery_days)

            order = PurchaseOrder(
                supplier_id=selected_sp.supplier.id,
                required_by_date=required_by,
                status=PurchaseOrderStatus.PENDING_APPROVAL,
                priority=priority,
                total_items=1,
                notes=f"Auto-generated by inventory monitor. Days remaining: {days_remaining:.1f}" if days_remaining is not None else "Auto-generated.",
            )
            db.add(order)
            await db.flush()

            item = PurchaseOrderItem(
                purchase_order_id=order.id,
                product_id=product.id,
                requested_quantity=reorder_qty,
                unit_price=getattr(selected_sp, "unit_price", None),
            )
            db.add(item)
            await db.flush()

            summary["orders_created"] += 1
            logger.info(
                "Auto-created PO #%s for %s: %.2f %s from %s (priority=%s)",
                order.id, product.product_name, reorder_qty, product.unit,
                selected_sp.supplier.supplier_name, priority.value,
            )

        except Exception as exc:
            logger.error(
                "Error checking product %s (id=%s): %s",
                product.product_name, product.id, exc, exc_info=True,
            )
            summary["errors"].append(f"Product {product.product_name}: {str(exc)}")

    logger.info(
        "Inventory check complete. Alerts created: %d, Orders created: %d",
        summary["alerts_created"], summary["orders_created"],
    )
    return summary

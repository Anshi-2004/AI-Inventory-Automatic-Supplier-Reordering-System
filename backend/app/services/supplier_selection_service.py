"""
Deterministic supplier selection logic — never delegated to LLM.

Selection criteria (in order of priority):
1. Supplier status = ACTIVE
2. Supplier has a relationship with the product (supplier_products table)
3. For EMERGENCY orders: prefer suppliers with emergency_available=True
4. Sort by: priority ASC (lower = better), delivery_days ASC, unit_price ASC
"""
from typing import Optional

from app.models.purchase_order import OrderPriority
from app.models.supplier_product import SupplierProduct


def select_best_supplier(
    supplier_products: list[SupplierProduct],
    is_emergency: bool = False,
) -> Optional[SupplierProduct]:
    """
    Given a list of SupplierProduct entries for a product,
    select the best supplier based on deterministic business rules.
    Returns None if no valid supplier exists.
    """
    if not supplier_products:
        return None

    # Filter: only active suppliers
    candidates = [
        sp for sp in supplier_products
        if sp.supplier and sp.supplier.status.value == "ACTIVE"
    ]
    if not candidates:
        return None

    if is_emergency:
        # Prefer suppliers with emergency availability
        emergency_candidates = [sp for sp in candidates if sp.emergency_available]
        if emergency_candidates:
            candidates = emergency_candidates
        # Sort emergency: delivery_days ASC, then priority ASC
        candidates.sort(key=lambda sp: (sp.delivery_days, sp.priority))
    else:
        # Normal: priority ASC, delivery_days ASC, unit_price ASC (None treated as high)
        candidates.sort(
            key=lambda sp: (
                sp.priority,
                sp.delivery_days,
                sp.unit_price if sp.unit_price is not None else float("inf"),
            )
        )

    return candidates[0] if candidates else None


def determine_order_priority(days_remaining: Optional[float], emergency_reserve_breached: bool) -> OrderPriority:
    """Map stock conditions to purchase order priority."""
    if emergency_reserve_breached or (days_remaining is not None and days_remaining <= 1):
        return OrderPriority.EMERGENCY
    elif days_remaining is not None and days_remaining <= 3:
        return OrderPriority.CRITICAL
    elif days_remaining is not None and days_remaining <= 7:
        return OrderPriority.HIGH
    else:
        return OrderPriority.NORMAL

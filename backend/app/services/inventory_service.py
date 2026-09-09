"""
Core inventory calculation business logic.
ALL calculations are done here — never inside the LLM.
"""
from typing import Optional

from app.config.settings import settings
from app.models.product import Product, ProductStatus


def calculate_days_remaining(product: Product) -> Optional[float]:
    """
    Calculate how many days the current stock will last.
    Returns None if no consumption data (average_daily_usage == 0).
    """
    if product.average_daily_usage <= 0:
        return None
    return product.current_quantity / product.average_daily_usage


def determine_product_status(product: Product) -> ProductStatus:
    """Deterministically compute the product status based on business rules."""
    from datetime import date

    # ── Expiry check ────────────────────────────────────────────────────────
    if product.expiry_date:
        today = date.today()
        if product.expiry_date < today:
            return ProductStatus.EXPIRED
        days_to_expiry = (product.expiry_date - today).days
        if days_to_expiry <= settings.expiry_warning_days:
            return ProductStatus.EXPIRING_SOON

    # ── Out of stock ─────────────────────────────────────────────────────────
    if product.current_quantity <= 0:
        return ProductStatus.OUT_OF_STOCK

    # ── No consumption data ───────────────────────────────────────────────────
    if product.average_daily_usage <= 0:
        return ProductStatus.NO_CONSUMPTION_DATA

    days_remaining = calculate_days_remaining(product)

    # ── Critical stock ────────────────────────────────────────────────────────
    if days_remaining is not None and days_remaining <= product.critical_days:
        return ProductStatus.CRITICAL

    # ── Low stock ─────────────────────────────────────────────────────────────
    if days_remaining is not None and days_remaining <= product.alert_days:
        return ProductStatus.LOW_STOCK

    return ProductStatus.ACTIVE


def is_emergency_stock(product: Product) -> bool:
    """Returns True if current stock has breached the emergency reserve."""
    return product.current_quantity <= product.emergency_reserve


def is_lead_time_risk(product: Product, supplier_delivery_days: int) -> bool:
    """
    Returns True if days_remaining is less than supplier delivery time
    plus safety buffer — meaning we may run out before delivery arrives.
    """
    days_remaining = calculate_days_remaining(product)
    if days_remaining is None:
        return False
    return days_remaining <= (supplier_delivery_days + settings.safety_buffer_days)

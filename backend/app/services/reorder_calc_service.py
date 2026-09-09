"""
Reorder quantity calculation — deterministic, never delegated to LLM.

Formula:
  required_stock = daily_usage × delivery_days + safety_stock
  reorder_qty    = max(required_stock - current_quantity, 0)
  reorder_qty    = max(reorder_qty, supplier_moq)
"""
from app.config.settings import settings
from app.models.product import Product
from app.models.supplier_product import SupplierProduct


def calculate_reorder_quantity(
    product: Product,
    supplier_product: SupplierProduct,
) -> float:
    """
    Returns the recommended reorder quantity for a product.
    Never negative. Always at least the supplier's minimum order quantity.
    """
    daily_usage = product.average_daily_usage
    delivery_days = supplier_product.delivery_days
    current_qty = product.current_quantity
    moq = supplier_product.minimum_order_quantity
    safety_stock = daily_usage * settings.safety_stock_days

    required_stock = daily_usage * delivery_days + safety_stock
    reorder_qty = max(required_stock - current_qty, 0.0)

    # Enforce supplier minimum order quantity
    if reorder_qty < moq:
        reorder_qty = moq

    return round(reorder_qty, 2)

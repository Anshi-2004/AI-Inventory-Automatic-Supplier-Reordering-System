# Import all models here so Alembic can detect them during autogenerate
from app.models.user import User, UserRole
from app.models.supplier import Supplier, SupplierStatus, SupplierPriority
from app.models.product import Product, ProductStatus
from app.models.supplier_product import SupplierProduct
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product_batch import ProductBatch
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus, OrderPriority
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.email_log import EmailLog, EmailStatus

__all__ = [
    "User", "UserRole",
    "Supplier", "SupplierStatus", "SupplierPriority",
    "Product", "ProductStatus",
    "SupplierProduct",
    "InventoryTransaction", "TransactionType",
    "ProductBatch",
    "PurchaseOrder", "PurchaseOrderStatus", "OrderPriority",
    "PurchaseOrderItem",
    "Alert", "AlertType", "AlertSeverity", "AlertStatus",
    "EmailLog", "EmailStatus",
]

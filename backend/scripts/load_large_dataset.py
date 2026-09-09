
import asyncio
import os
import sys
import csv
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.models.user import User, UserRole
from app.models.supplier import Supplier, SupplierPriority, SupplierStatus
from app.models.product import Product, ProductStatus
from app.models.supplier_product import SupplierProduct
from app.models.product_batch import ProductBatch
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus, OrderPriority
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.alert import Alert
from app.models.email_log import EmailLog

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dataset path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_DIR = os.path.join(WORKSPACE_ROOT, "dataset")

def parse_datetime(val: str) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        return None

def parse_date(val: str) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None

def parse_bool(val: str) -> bool:
    return val.lower() == 'true'

def parse_float(val: str) -> float:
    return float(val) if val else 0.0

def parse_int(val: str) -> int:
    return int(val) if val else 0

async def load_users(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "users.csv")
    print(f"Loading users from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = User(
                id=parse_int(row["id"]),
                name=row["name"],
                email=row["email"],
                password_hash=row["password_hash"],
                role=UserRole(row["role"]),
                is_active=parse_bool(row["is_active"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(user)
    await db.flush()

async def load_suppliers(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "suppliers.csv")
    print(f"Loading suppliers from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            supplier = Supplier(
                id=parse_int(row["id"]),
                supplier_name=row["supplier_name"],
                company_name=row["company_name"],
                email=row["email"],
                phone=row["phone"] or None,
                address=row["address"] or None,
                preferred_contact_method=row["preferred_contact_method"],
                average_delivery_days=parse_int(row["average_delivery_days"]),
                emergency_available=parse_bool(row["emergency_available"]),
                priority=SupplierPriority(row["priority"]),
                status=SupplierStatus(row["status"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(supplier)
    await db.flush()

async def load_products(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "products.csv")
    print(f"Loading products from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = Product(
                id=parse_int(row["id"]),
                product_name=row["product_name"],
                product_code=row["product_code"],
                category=row["category"],
                description=row["description"] or None,
                current_quantity=parse_float(row["current_quantity"]),
                unit=row["unit"],
                minimum_stock=parse_float(row["minimum_stock"]),
                average_daily_usage=parse_float(row["average_daily_usage"]),
                alert_days=parse_int(row["alert_days"]),
                critical_days=parse_int(row["critical_days"]),
                emergency_reserve=parse_float(row["emergency_reserve"]),
                expiry_date=parse_date(row["expiry_date"]),
                storage_location=row["storage_location"] or None,
                primary_supplier_id=parse_int(row["primary_supplier_id"]) if row["primary_supplier_id"] else None,
                status=ProductStatus(row["status"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(product)
    await db.flush()

async def load_supplier_products(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "supplier_products.csv")
    print(f"Loading supplier products from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sp = SupplierProduct(
                id=parse_int(row["id"]),
                supplier_id=parse_int(row["supplier_id"]),
                product_id=parse_int(row["product_id"]),
                unit_price=parse_float(row["unit_price"]) if row["unit_price"] else None,
                minimum_order_quantity=parse_float(row["minimum_order_quantity"]),
                delivery_days=parse_int(row["delivery_days"]),
                priority=parse_int(row["priority"]),
                emergency_available=parse_bool(row["emergency_available"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(sp)
    await db.flush()

async def load_product_batches(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "product_batches.csv")
    print(f"Loading product batches from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pb = ProductBatch(
                id=parse_int(row["id"]),
                product_id=parse_int(row["product_id"]),
                batch_number=row["batch_number"],
                quantity=parse_float(row["quantity"]),
                manufacturing_date=parse_date(row["manufacturing_date"]),
                expiry_date=parse_date(row["expiry_date"]),
                received_date=parse_date(row["received_date"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(pb)
    await db.flush()

async def load_inventory_transactions(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "inventory_transactions.csv")
    print(f"Loading inventory transactions from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tx = InventoryTransaction(
                id=parse_int(row["id"]),
                product_id=parse_int(row["product_id"]),
                transaction_type=TransactionType(row["transaction_type"]),
                quantity=parse_float(row["quantity"]),
                stock_after=parse_float(row["stock_after"]) if row["stock_after"] else None,
                reason=row["reason"] or None,
                reference_id=row["reference_id"] or None,
                batch_id=parse_int(row["batch_id"]) if row["batch_id"] else None,
                transaction_date=parse_datetime(row["transaction_date"]),
                created_by=parse_int(row["created_by"]) if row["created_by"] else None,
                created_at=parse_datetime(row["created_at"])
            )
            db.add(tx)
    await db.flush()

async def load_purchase_orders(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "purchase_orders.csv")
    print(f"Loading purchase orders from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            po = PurchaseOrder(
                id=parse_int(row["id"]),
                supplier_id=parse_int(row["supplier_id"]),
                order_date=parse_datetime(row["order_date"]),
                required_by_date=parse_datetime(row["required_by_date"]),
                status=PurchaseOrderStatus(row["status"]),
                priority=OrderPriority(row["priority"]),
                total_items=parse_int(row["total_items"]),
                notes=row["notes"] or None,
                created_by=parse_int(row["created_by"]) if row["created_by"] else None,
                approved_by=parse_int(row["approved_by"]) if row["approved_by"] else None,
                approved_at=parse_datetime(row["approved_at"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(po)
    await db.flush()

async def load_purchase_order_items(db: AsyncSession):
    filepath = os.path.join(DATASET_DIR, "purchase_order_items.csv")
    print(f"Loading purchase order items from {filepath}...")
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            poi = PurchaseOrderItem(
                id=parse_int(row["id"]),
                purchase_order_id=parse_int(row["purchase_order_id"]),
                product_id=parse_int(row["product_id"]),
                requested_quantity=parse_float(row["requested_quantity"]),
                received_quantity=parse_float(row["received_quantity"]),
                unit_price=parse_float(row["unit_price"]) if row["unit_price"] else None,
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"])
            )
            db.add(poi)
    await db.flush()

async def load_all():
    async with SessionLocal() as db:
        print("🗑️ Clearing existing data...")
        await db.execute(delete(EmailLog))
        await db.execute(delete(Alert))
        await db.execute(delete(PurchaseOrderItem))
        await db.execute(delete(PurchaseOrder))
        await db.execute(delete(InventoryTransaction))
        await db.execute(delete(ProductBatch))
        await db.execute(delete(SupplierProduct))
        await db.execute(delete(Product))
        await db.execute(delete(Supplier))
        await db.execute(delete(User))
        await db.flush()
        print("✅ Tables cleared.")

        print("🌱 Seeding large dataset...")
        await load_users(db)
        await load_suppliers(db)
        await load_products(db)
        await load_supplier_products(db)
        await load_product_batches(db)
        await load_inventory_transactions(db)
        await load_purchase_orders(db)
        await load_purchase_order_items(db)

        await db.commit()
        print("\n🎉 Large dataset import complete!")

if __name__ == "__main__":
    asyncio.run(load_all())

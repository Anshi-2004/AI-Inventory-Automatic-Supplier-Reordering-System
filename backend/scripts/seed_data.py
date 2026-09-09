"""
Seed data script: creates realistic sample data for immediate demo.
Suppliers, products, supplier-product links, inventory transactions.

Usage:
    cd backend
    python scripts/seed_data.py
"""
import asyncio
import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from passlib.context import CryptContext

from app.config.settings import settings
from app.models.user import User, UserRole
from app.models.supplier import Supplier, SupplierPriority, SupplierStatus
from app.models.product import Product, ProductStatus
from app.models.supplier_product import SupplierProduct
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product_batch import ProductBatch

from app.database.base import Base
import app.models  # noqa: F401

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("Seeding database...")

        # ── Users ─────────────────────────────────────────────────────────────
        admin = User(
            name="Admin User",
            email="admin@inventory.com",
            password_hash=pwd_context.hash("Admin@1234"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            name="Inventory Manager",
            email="manager@inventory.com",
            password_hash=pwd_context.hash("Manager@1234"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        db.add_all([admin, manager])
        await db.flush()
        print(f"  [Users] admin@inventory.com (Admin@1234), manager@inventory.com (Manager@1234)")

        # ── Suppliers ─────────────────────────────────────────────────────────
        abc_medical = Supplier(
            supplier_name="ABC Medical Store",
            company_name="ABC Medical Supplies Pvt Ltd",
            email="orders@abcmedical.com",
            phone="+91-9876543210",
            address="123 Medical District, Mumbai, Maharashtra",
            preferred_contact_method="email",
            average_delivery_days=5,
            emergency_available=True,
            priority=SupplierPriority.PREFERRED,
            status=SupplierStatus.ACTIVE,
        )
        xyz_healthcare = Supplier(
            supplier_name="XYZ Healthcare",
            company_name="XYZ Healthcare Solutions Ltd",
            email="supply@xyzhealthcare.com",
            phone="+91-9871234560",
            address="456 Health Zone, Delhi, NCR",
            preferred_contact_method="email",
            average_delivery_days=7,
            emergency_available=True,
            priority=SupplierPriority.HIGH,
            status=SupplierStatus.ACTIVE,
        )
        raj_suppliers = Supplier(
            supplier_name="Raj Suppliers",
            company_name="Raj Medical & General Suppliers",
            email="raj@rajsuppliers.com",
            phone="+91-9812345670",
            address="789 Market Road, Pune, Maharashtra",
            preferred_contact_method="phone",
            average_delivery_days=10,
            emergency_available=False,
            priority=SupplierPriority.MEDIUM,
            status=SupplierStatus.ACTIVE,
        )
        db.add_all([abc_medical, xyz_healthcare, raj_suppliers])
        await db.flush()
        print(f"  [Suppliers] ABC Medical, XYZ Healthcare, Raj Suppliers")

        # ── Products ─────────────────────────────────────────────────────────
        paracetamol = Product(
            product_name="Paracetamol",
            product_code="MED-PCM-500",
            category="Medicines",
            description="Paracetamol 500mg tablets for pain and fever relief",
            current_quantity=10.0,
            unit="units",
            minimum_stock=20.0,
            average_daily_usage=2.0,    # 2 units/day → 5 days remaining
            alert_days=7,               # alert when < 7 days
            critical_days=3,
            emergency_reserve=5.0,
            expiry_date=date.today() + timedelta(days=180),
            storage_location="Shelf A-1",
            status=ProductStatus.LOW_STOCK,
            primary_supplier_id=abc_medical.id,
        )
        syringes = Product(
            product_name="Syringes (5ml)",
            product_code="INJ-SYR-5ML",
            category="Medical Supplies",
            description="5ml disposable syringes, sterile",
            current_quantity=150.0,
            unit="pieces",
            minimum_stock=100.0,
            average_daily_usage=10.0,   # 15 days remaining
            alert_days=7,
            critical_days=3,
            emergency_reserve=30.0,
            expiry_date=date.today() + timedelta(days=365),
            storage_location="Shelf B-2",
            status=ProductStatus.ACTIVE,
            primary_supplier_id=xyz_healthcare.id,
        )
        gloves = Product(
            product_name="Latex Gloves (M)",
            product_code="PPE-GLV-M",
            category="PPE",
            description="Medium size latex examination gloves, box of 100",
            current_quantity=3.0,       # 3 boxes, only 3 days remaining (1/day)
            unit="boxes",
            minimum_stock=5.0,
            average_daily_usage=1.0,
            alert_days=7,
            critical_days=3,
            emergency_reserve=1.0,
            storage_location="Shelf C-3",
            status=ProductStatus.CRITICAL,
            primary_supplier_id=raj_suppliers.id,
        )
        bandages = Product(
            product_name="Bandage Rolls (4-inch)",
            product_code="SURG-BND-4",
            category="Surgical",
            description="4-inch elastic bandage rolls",
            current_quantity=200.0,
            unit="rolls",
            minimum_stock=50.0,
            average_daily_usage=5.0,    # 40 days remaining
            alert_days=7,
            critical_days=3,
            emergency_reserve=10.0,
            expiry_date=date.today() + timedelta(days=25),  # expiring soon!
            storage_location="Shelf D-4",
            status=ProductStatus.EXPIRING_SOON,
            primary_supplier_id=abc_medical.id,
        )
        ibuprofen = Product(
            product_name="Ibuprofen 400mg",
            product_code="MED-IBU-400",
            category="Medicines",
            description="Ibuprofen 400mg tablets — NSAID pain reliever",
            current_quantity=0.0,
            unit="units",
            minimum_stock=50.0,
            average_daily_usage=3.0,
            alert_days=7,
            critical_days=3,
            emergency_reserve=15.0,
            storage_location="Shelf A-2",
            status=ProductStatus.OUT_OF_STOCK,
            primary_supplier_id=abc_medical.id,
        )
        db.add_all([paracetamol, syringes, gloves, bandages, ibuprofen])
        await db.flush()
        print(f"  [Products] Paracetamol, Syringes, Gloves, Bandages, Ibuprofen")

        # ── Supplier-Product Links ────────────────────────────────────────────
        links = [
            # Paracetamol — ABC (preferred), XYZ (backup)
            SupplierProduct(supplier_id=abc_medical.id, product_id=paracetamol.id,
                            unit_price=2.5, minimum_order_quantity=100, delivery_days=5,
                            priority=1, emergency_available=True),
            SupplierProduct(supplier_id=xyz_healthcare.id, product_id=paracetamol.id,
                            unit_price=2.8, minimum_order_quantity=50, delivery_days=7,
                            priority=2, emergency_available=True),
            # Syringes — XYZ (preferred), Raj (backup)
            SupplierProduct(supplier_id=xyz_healthcare.id, product_id=syringes.id,
                            unit_price=8.0, minimum_order_quantity=50, delivery_days=7,
                            priority=1, emergency_available=True),
            SupplierProduct(supplier_id=raj_suppliers.id, product_id=syringes.id,
                            unit_price=9.0, minimum_order_quantity=100, delivery_days=10,
                            priority=2, emergency_available=False),
            # Gloves — Raj (preferred), ABC (backup)
            SupplierProduct(supplier_id=raj_suppliers.id, product_id=gloves.id,
                            unit_price=350.0, minimum_order_quantity=5, delivery_days=10,
                            priority=1, emergency_available=False),
            SupplierProduct(supplier_id=abc_medical.id, product_id=gloves.id,
                            unit_price=380.0, minimum_order_quantity=3, delivery_days=5,
                            priority=2, emergency_available=True),
            # Bandages — ABC
            SupplierProduct(supplier_id=abc_medical.id, product_id=bandages.id,
                            unit_price=15.0, minimum_order_quantity=50, delivery_days=5,
                            priority=1, emergency_available=True),
            # Ibuprofen — ABC, XYZ
            SupplierProduct(supplier_id=abc_medical.id, product_id=ibuprofen.id,
                            unit_price=3.0, minimum_order_quantity=100, delivery_days=5,
                            priority=1, emergency_available=True),
            SupplierProduct(supplier_id=xyz_healthcare.id, product_id=ibuprofen.id,
                            unit_price=3.2, minimum_order_quantity=50, delivery_days=7,
                            priority=2, emergency_available=False),
        ]
        db.add_all(links)
        await db.flush()
        print(f"  Supplier-product links created")

        # ── Inventory Transactions (history) ──────────────────────────────────
        txns = [
            InventoryTransaction(product_id=paracetamol.id, transaction_type=TransactionType.IN,
                                 quantity=100.0, stock_after=100.0, reason="Initial stock",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=45)),
            InventoryTransaction(product_id=paracetamol.id, transaction_type=TransactionType.OUT,
                                 quantity=90.0, stock_after=10.0, reason="Daily usage",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=1)),
            InventoryTransaction(product_id=syringes.id, transaction_type=TransactionType.IN,
                                 quantity=300.0, stock_after=300.0, reason="Initial stock",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=30)),
            InventoryTransaction(product_id=syringes.id, transaction_type=TransactionType.OUT,
                                 quantity=150.0, stock_after=150.0, reason="Usage",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=1)),
            InventoryTransaction(product_id=gloves.id, transaction_type=TransactionType.IN,
                                 quantity=20.0, stock_after=20.0, reason="Initial stock",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=20)),
            InventoryTransaction(product_id=gloves.id, transaction_type=TransactionType.OUT,
                                 quantity=17.0, stock_after=3.0, reason="Daily consumption",
                                 transaction_date=datetime.now(timezone.utc) - timedelta(days=1)),
        ]
        db.add_all(txns)
        await db.flush()
        print(f"  Inventory transactions created")

        # ── Product Batches (for FEFO) ─────────────────────────────────────────
        batches = [
            ProductBatch(product_id=paracetamol.id, batch_number="PCM-2024-001",
                         quantity=10.0, received_date=date.today() - timedelta(days=45),
                         expiry_date=date.today() + timedelta(days=180)),
            ProductBatch(product_id=syringes.id, batch_number="SYR-2024-001",
                         quantity=150.0, received_date=date.today() - timedelta(days=30),
                         expiry_date=date.today() + timedelta(days=365)),
            ProductBatch(product_id=gloves.id, batch_number="GLV-2024-001",
                         quantity=3.0, received_date=date.today() - timedelta(days=20),
                         expiry_date=date.today() + timedelta(days=90)),
            ProductBatch(product_id=bandages.id, batch_number="BND-2024-001",
                         quantity=200.0, received_date=date.today() - timedelta(days=5),
                         expiry_date=date.today() + timedelta(days=25)),
        ]
        db.add_all(batches)
        await db.flush()

        await db.commit()
        print("\nSeed data complete!")
        print("\nLogin credentials:")
        print("   Admin:   admin@inventory.com    / Admin@1234")
        print("   Manager: manager@inventory.com  / Manager@1234")
        print("\nProducts seeded:")
        print("   - Paracetamol  - LOW STOCK (5 days remaining)")
        print("   - Syringes     - ACTIVE (15 days remaining)")
        print("   - Latex Gloves - CRITICAL (3 days remaining)")
        print("   - Bandages     - EXPIRING SOON (25 days to expiry)")
        print("   - Ibuprofen    - OUT OF STOCK")


if __name__ == "__main__":
    asyncio.run(seed())

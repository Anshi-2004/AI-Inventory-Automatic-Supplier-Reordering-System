import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOW_STOCK = "LOW_STOCK"
    CRITICAL = "CRITICAL"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    EXPIRED = "EXPIRED"
    EXPIRING_SOON = "EXPIRING_SOON"
    NO_CONSUMPTION_DATA = "NO_CONSUMPTION_DATA"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Stock fields ──────────────────────────────────────────────────────────
    current_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="units")
    minimum_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_daily_usage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Threshold fields ──────────────────────────────────────────────────────
    alert_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)   # days
    critical_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # days
    emergency_reserve: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Expiry ────────────────────────────────────────────────────────────────
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Logistics ─────────────────────────────────────────────────────────────
    storage_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_supplier_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("suppliers.id", name="fk_products_primary_supplier_id_suppliers"), nullable=True
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="productstatus"),
        default=ProductStatus.ACTIVE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    primary_supplier: Mapped["Supplier | None"] = relationship(
        "Supplier", foreign_keys=[primary_supplier_id]
    )
    supplier_products: Mapped[list["SupplierProduct"]] = relationship(
        "SupplierProduct", back_populates="product", cascade="all, delete-orphan"
    )
    inventory_transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="product"
    )
    product_batches: Mapped[list["ProductBatch"]] = relationship(
        "ProductBatch", back_populates="product", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="product"
    )
    purchase_order_items: Mapped[list["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} code={self.product_code} name={self.product_name}>"

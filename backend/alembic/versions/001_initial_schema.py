"""Initial schema - all 10 tables

Revision ID: 001
Revises: 
Create Date: 2026-08-11
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    userrole = sa.Enum("ADMIN", "INVENTORY_MANAGER", name="userrole")
    supplierstatus = sa.Enum("ACTIVE", "INACTIVE", name="supplierstatus")
    supplierpriority = sa.Enum("LOW", "MEDIUM", "HIGH", "PREFERRED", name="supplierpriority")
    productstatus = sa.Enum(
        "ACTIVE", "LOW_STOCK", "CRITICAL", "OUT_OF_STOCK",
        "EXPIRED", "EXPIRING_SOON", "NO_CONSUMPTION_DATA", name="productstatus"
    )
    transactiontype = sa.Enum(
        "IN", "OUT", "ADJUSTMENT", "DAMAGE", "EXPIRED", "RETURN", name="transactiontype"
    )
    purchaseorderstatus = sa.Enum(
        "DRAFT", "PENDING_APPROVAL", "APPROVED", "EMAIL_GENERATED",
        "EMAIL_SENT", "CONFIRMED", "DISPATCHED", "DELIVERED", "CANCELLED",
        name="purchaseorderstatus"
    )
    orderpriority = sa.Enum("NORMAL", "HIGH", "CRITICAL", "EMERGENCY", name="orderpriority")
    alerttype = sa.Enum(
        "LOW_STOCK", "CRITICAL_STOCK", "OUT_OF_STOCK", "EXPIRING_SOON",
        "EXPIRED", "EMERGENCY_STOCK", "SUPPLIER_DELAY", name="alerttype"
    )
    alertseverity = sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="alertseverity")
    alertstatus = sa.Enum("ACTIVE", "RESOLVED", "DISMISSED", name="alertstatus")
    emailstatus = sa.Enum("DRAFT", "APPROVED", "SENT", "FAILED", name="emailstatus")

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False, server_default="INVENTORY_MANAGER"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── suppliers ─────────────────────────────────────────────────────────────
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("supplier_name", sa.String(200), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("preferred_contact_method", sa.String(50), nullable=False, server_default="email"),
        sa.Column("average_delivery_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("emergency_available", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("priority", supplierpriority, nullable=False, server_default="MEDIUM"),
        sa.Column("status", supplierstatus, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_suppliers_email"),
    )
    op.create_index("ix_suppliers_id", "suppliers", ["id"])
    op.create_index("ix_suppliers_email", "suppliers", ["email"])

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("current_quantity", sa.Float, nullable=False, server_default="0"),
        sa.Column("unit", sa.String(30), nullable=False, server_default="units"),
        sa.Column("minimum_stock", sa.Float, nullable=False, server_default="0"),
        sa.Column("average_daily_usage", sa.Float, nullable=False, server_default="0"),
        sa.Column("alert_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("critical_days", sa.Integer, nullable=False, server_default="3"),
        sa.Column("emergency_reserve", sa.Float, nullable=False, server_default="0"),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("storage_location", sa.String(100), nullable=True),
        sa.Column("primary_supplier_id", sa.Integer, sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("status", productstatus, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("product_code", name="uq_products_product_code"),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_product_code", "products", ["product_code"])
    op.create_index("ix_products_product_name", "products", ["product_name"])

    # ── product_batches ───────────────────────────────────────────────────────
    op.create_table(
        "product_batches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_number", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False, server_default="0"),
        sa.Column("manufacturing_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("received_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_product_batches_id", "product_batches", ["id"])
    op.create_index("ix_product_batches_expiry_date", "product_batches", ["expiry_date"])

    # ── supplier_products ─────────────────────────────────────────────────────
    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_price", sa.Float, nullable=True),
        sa.Column("minimum_order_quantity", sa.Float, nullable=False, server_default="1"),
        sa.Column("delivery_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="1"),
        sa.Column("emergency_available", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_supplier_products_id", "supplier_products", ["id"])
    op.create_index("ix_supplier_products_supplier_id", "supplier_products", ["supplier_id"])
    op.create_index("ix_supplier_products_product_id", "supplier_products", ["product_id"])

    # ── inventory_transactions ────────────────────────────────────────────────
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_type", transactiontype, nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("stock_after", sa.Float, nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("batch_id", sa.Integer, sa.ForeignKey("product_batches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_transactions_id", "inventory_transactions", ["id"])
    op.create_index("ix_inventory_transactions_product_id", "inventory_transactions", ["product_id"])

    # ── purchase_orders ───────────────────────────────────────────────────────
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("required_by_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", purchaseorderstatus, nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("priority", orderpriority, nullable=False, server_default="NORMAL"),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_orders_id", "purchase_orders", ["id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])

    # ── purchase_order_items ──────────────────────────────────────────────────
    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("purchase_order_id", sa.Integer, sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requested_quantity", sa.Float, nullable=False),
        sa.Column("received_quantity", sa.Float, nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_order_items_id", "purchase_order_items", ["id"])

    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", alerttype, nullable=False),
        sa.Column("current_stock", sa.Float, nullable=False),
        sa.Column("daily_usage", sa.Float, nullable=False),
        sa.Column("days_remaining", sa.Float, nullable=True),
        sa.Column("threshold", sa.Float, nullable=True),
        sa.Column("severity", alertseverity, nullable=False, server_default="MEDIUM"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", alertstatus, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_index("ix_alerts_product_id", "alerts", ["product_id"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_status", "alerts", ["status"])

    # ── email_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("purchase_order_id", sa.Integer, sa.ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", emailstatus, nullable=False, server_default="DRAFT"),
        sa.Column("generated_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_email_logs_id", "email_logs", ["id"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index("ix_email_logs_purchase_order_id", "email_logs", ["purchase_order_id"])


def downgrade() -> None:
    op.drop_table("email_logs")
    op.drop_table("alerts")
    op.drop_table("purchase_order_items")
    op.drop_table("purchase_orders")
    op.drop_table("inventory_transactions")
    op.drop_table("supplier_products")
    op.drop_table("product_batches")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("users")

    for enum_name in [
        "userrole", "supplierstatus", "supplierpriority", "productstatus",
        "transactiontype", "purchaseorderstatus", "orderpriority",
        "alerttype", "alertseverity", "alertstatus", "emailstatus",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)

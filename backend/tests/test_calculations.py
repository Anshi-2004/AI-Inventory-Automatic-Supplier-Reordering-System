"""
Tests for all core inventory business calculation rules.
These are pure unit tests — no DB or API calls.
"""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from app.services.inventory_service import (
    calculate_days_remaining,
    determine_product_status,
    is_emergency_stock,
    is_lead_time_risk,
)
from app.services.reorder_calc_service import calculate_reorder_quantity
from app.services.supplier_selection_service import (
    select_best_supplier,
    determine_order_priority,
)
from app.models.product import Product, ProductStatus
from app.models.purchase_order import OrderPriority


def make_product(**kwargs) -> Product:
    defaults = {
        "id": 1,
        "product_name": "Test Product",
        "product_code": "TEST-001",
        "category": "Test",
        "current_quantity": 10.0,
        "unit": "units",
        "average_daily_usage": 2.0,
        "alert_days": 7,
        "critical_days": 3,
        "emergency_reserve": 5.0,
        "minimum_stock": 10.0,
        "expiry_date": None,
        "status": ProductStatus.ACTIVE,
    }
    defaults.update(kwargs)
    p = MagicMock(spec=Product)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def make_supplier_product(**kwargs):
    sp = MagicMock()
    defaults = {
        "delivery_days": 5,
        "minimum_order_quantity": 10.0,
        "unit_price": 5.0,
        "priority": 1,
        "emergency_available": False,
        "supplier": MagicMock(status=MagicMock(value="ACTIVE")),
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(sp, k, v)
    return sp


# ── Days remaining ─────────────────────────────────────────────────────────────

def test_days_remaining_basic():
    p = make_product(current_quantity=10, average_daily_usage=2)
    assert calculate_days_remaining(p) == 5.0


def test_days_remaining_zero_usage():
    p = make_product(current_quantity=10, average_daily_usage=0)
    assert calculate_days_remaining(p) is None


def test_days_remaining_zero_stock():
    p = make_product(current_quantity=0, average_daily_usage=2)
    assert calculate_days_remaining(p) == 0.0


# ── Low stock detection ───────────────────────────────────────────────────────

def test_low_stock_detected():
    p = make_product(current_quantity=10, average_daily_usage=2, alert_days=7)
    status = determine_product_status(p)
    # 10/2 = 5 days, alert at 7 → LOW_STOCK
    assert status == ProductStatus.LOW_STOCK


def test_active_status():
    p = make_product(current_quantity=100, average_daily_usage=2, alert_days=7)
    status = determine_product_status(p)
    # 100/2 = 50 days > 7 → ACTIVE
    assert status == ProductStatus.ACTIVE


# ── Critical stock detection ─────────────────────────────────────────────────

def test_critical_stock_detected():
    p = make_product(current_quantity=4, average_daily_usage=2, alert_days=7, critical_days=3)
    status = determine_product_status(p)
    # 4/2 = 2 days ≤ 3 critical_days → CRITICAL
    assert status == ProductStatus.CRITICAL


# ── Emergency stock detection ─────────────────────────────────────────────────

def test_emergency_stock_detected():
    p = make_product(current_quantity=4, emergency_reserve=5)
    assert is_emergency_stock(p) is True


def test_no_emergency_stock():
    p = make_product(current_quantity=10, emergency_reserve=5)
    assert is_emergency_stock(p) is False


# ── Expiry detection ──────────────────────────────────────────────────────────

def test_expiry_detected():
    p = make_product(expiry_date=date.today() - timedelta(days=1))
    status = determine_product_status(p)
    assert status == ProductStatus.EXPIRED


def test_expiring_soon_detected():
    p = make_product(expiry_date=date.today() + timedelta(days=15))
    status = determine_product_status(p)
    assert status == ProductStatus.EXPIRING_SOON


# ── Lead time risk ────────────────────────────────────────────────────────────

def test_lead_time_risk_detected():
    p = make_product(current_quantity=8, average_daily_usage=2)  # 4 days remaining
    # supplier delivery = 5 days, safety buffer = 2 → risk if 4 ≤ 7
    assert is_lead_time_risk(p, supplier_delivery_days=5) is True


def test_no_lead_time_risk():
    p = make_product(current_quantity=100, average_daily_usage=2)  # 50 days remaining
    assert is_lead_time_risk(p, supplier_delivery_days=5) is False


# ── Reorder quantity ─────────────────────────────────────────────────────────

def test_reorder_quantity_basic():
    p = make_product(current_quantity=10, average_daily_usage=2)
    sp = make_supplier_product(delivery_days=5, minimum_order_quantity=10)
    # required = 2*5 + 2*7 = 10 + 14 = 24; reorder = 24 - 10 = 14; MOQ=10 → 14
    qty = calculate_reorder_quantity(p, sp)
    assert qty >= 10  # at least MOQ
    assert qty > 0


def test_reorder_quantity_enforces_moq():
    p = make_product(current_quantity=90, average_daily_usage=1)
    sp = make_supplier_product(delivery_days=5, minimum_order_quantity=100)
    # Very small need but MOQ=100
    qty = calculate_reorder_quantity(p, sp)
    assert qty == 100.0


def test_reorder_quantity_never_negative():
    p = make_product(current_quantity=1000, average_daily_usage=1)
    sp = make_supplier_product(delivery_days=5, minimum_order_quantity=1)
    qty = calculate_reorder_quantity(p, sp)
    assert qty >= 0


# ── Supplier selection ────────────────────────────────────────────────────────

def test_supplier_selection_normal():
    sp1 = make_supplier_product(priority=2, delivery_days=7, emergency_available=False)
    sp2 = make_supplier_product(priority=1, delivery_days=5, emergency_available=True)
    selected = select_best_supplier([sp1, sp2], is_emergency=False)
    assert selected is sp2  # lower priority number wins


def test_supplier_selection_emergency():
    sp1 = make_supplier_product(priority=1, delivery_days=10, emergency_available=False)
    sp2 = make_supplier_product(priority=2, delivery_days=3, emergency_available=True)
    selected = select_best_supplier([sp1, sp2], is_emergency=True)
    assert selected is sp2  # emergency-available + shortest delivery


def test_supplier_selection_no_suppliers():
    selected = select_best_supplier([])
    assert selected is None


# ── Order priority ────────────────────────────────────────────────────────────

def test_order_priority_emergency():
    assert determine_order_priority(0.5, False) == OrderPriority.EMERGENCY


def test_order_priority_critical():
    assert determine_order_priority(2.0, False) == OrderPriority.CRITICAL


def test_order_priority_high():
    assert determine_order_priority(5.0, False) == OrderPriority.HIGH


def test_order_priority_normal():
    assert determine_order_priority(15.0, False) == OrderPriority.NORMAL

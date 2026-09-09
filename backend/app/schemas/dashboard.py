from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_products: int
    total_suppliers: int
    low_stock_count: int
    critical_count: int
    out_of_stock_count: int
    emergency_count: int
    expiring_soon_count: int
    expired_count: int
    active_alerts: int
    pending_orders: int
    emails_sent: int
    emails_draft: int

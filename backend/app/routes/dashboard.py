from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.alert import Alert, AlertStatus
from app.models.email_log import EmailLog, EmailStatus
from app.models.product import Product, ProductStatus
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Dashboard overview metrics")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all metrics needed for the dashboard overview cards."""

    async def count(stmt):
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await db.execute(count_stmt)
        return result.scalar_one()

    total_products = await count(select(Product))
    total_suppliers = await count(select(Supplier))

    low_stock = await count(select(Product).where(Product.status == ProductStatus.LOW_STOCK))
    critical = await count(select(Product).where(Product.status == ProductStatus.CRITICAL))
    out_of_stock = await count(select(Product).where(Product.status == ProductStatus.OUT_OF_STOCK))
    expiring_soon = await count(select(Product).where(Product.status == ProductStatus.EXPIRING_SOON))
    expired = await count(select(Product).where(Product.status == ProductStatus.EXPIRED))

    # Emergency stock: products where current_quantity <= emergency_reserve AND reserve > 0
    emergency_result = await db.execute(
        select(Product).where(
            Product.emergency_reserve > 0,
            Product.current_quantity <= Product.emergency_reserve,
        )
    )
    emergency_count = len(emergency_result.scalars().all())

    active_alerts = await count(select(Alert).where(Alert.status == AlertStatus.ACTIVE))

    pending_orders = await count(
        select(PurchaseOrder).where(
            PurchaseOrder.status.in_([
                PurchaseOrderStatus.PENDING_APPROVAL,
                PurchaseOrderStatus.APPROVED,
                PurchaseOrderStatus.EMAIL_GENERATED,
            ])
        )
    )

    emails_sent = await count(select(EmailLog).where(EmailLog.status == EmailStatus.SENT))
    emails_draft = await count(
        select(EmailLog).where(EmailLog.status.in_([EmailStatus.DRAFT, EmailStatus.APPROVED]))
    )

    return DashboardSummary(
        total_products=total_products,
        total_suppliers=total_suppliers,
        low_stock_count=low_stock,
        critical_count=critical,
        out_of_stock_count=out_of_stock,
        emergency_count=emergency_count,
        expiring_soon_count=expiring_soon,
        expired_count=expired,
        active_alerts=active_alerts,
        pending_orders=pending_orders,
        emails_sent=emails_sent,
        emails_draft=emails_draft,
    )

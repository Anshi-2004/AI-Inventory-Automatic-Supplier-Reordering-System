"""
Expiry management service.
Checks product expiry dates and creates appropriate alerts.
"""
import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from app.models.product import Product, ProductStatus
from app.repositories.alert_repo import AlertRepository
from app.repositories.inventory_repo import InventoryRepository

logger = logging.getLogger(__name__)


class ExpiryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_repo = AlertRepository(db)
        self.inv_repo = InventoryRepository(db)

    async def check_product_expiry(self, product: Product) -> list[Alert]:
        """Check a single product for expiry conditions. Returns created alerts."""
        alerts_created = []
        today = date.today()

        if not product.expiry_date:
            return []

        days_to_expiry = (product.expiry_date - today).days

        if product.expiry_date < today:
            # Already expired
            if not await self.alert_repo.has_active_alert(product.id, AlertType.EXPIRED):
                alert = Alert(
                    product_id=product.id,
                    alert_type=AlertType.EXPIRED,
                    current_stock=product.current_quantity,
                    daily_usage=product.average_daily_usage,
                    days_remaining=None,
                    severity=AlertSeverity.CRITICAL,
                    message=(
                        f"{product.product_name} (code: {product.product_code}) expired on "
                        f"{product.expiry_date}. Current stock: {product.current_quantity} {product.unit}. "
                        "Do not use this stock."
                    ),
                    status=AlertStatus.ACTIVE,
                )
                alert = await self.alert_repo.create(alert)
                alerts_created.append(alert)
                product.status = ProductStatus.EXPIRED
                logger.warning("EXPIRED alert for product %s", product.product_name)

        elif days_to_expiry <= settings.expiry_warning_days:
            # Expiring soon
            if not await self.alert_repo.has_active_alert(product.id, AlertType.EXPIRING_SOON):
                severity = AlertSeverity.HIGH if days_to_expiry <= 7 else AlertSeverity.MEDIUM
                alert = Alert(
                    product_id=product.id,
                    alert_type=AlertType.EXPIRING_SOON,
                    current_stock=product.current_quantity,
                    daily_usage=product.average_daily_usage,
                    days_remaining=float(days_to_expiry),
                    threshold=float(settings.expiry_warning_days),
                    severity=severity,
                    message=(
                        f"{product.product_name} will expire in {days_to_expiry} days "
                        f"(on {product.expiry_date}). Current stock: {product.current_quantity} {product.unit}."
                    ),
                    status=AlertStatus.ACTIVE,
                )
                alert = await self.alert_repo.create(alert)
                alerts_created.append(alert)
                product.status = ProductStatus.EXPIRING_SOON
                logger.info("EXPIRING_SOON alert for product %s", product.product_name)

        return alerts_created

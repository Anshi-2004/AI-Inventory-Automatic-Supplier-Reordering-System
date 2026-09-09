"""
Alert service: creates alerts based on business rules.
All thresholds are computed by business logic (never the LLM).
"""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from app.models.product import Product
from app.repositories.alert_repo import AlertRepository
from app.services.inventory_service import calculate_days_remaining, is_emergency_stock

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AlertRepository(db)

    async def check_and_create_alerts(self, product: Product) -> list[Alert]:
        """
        Evaluate a product against all stock alert rules.
        Creates alerts only if no active alert of the same type exists (dedup).
        Returns list of newly created alerts.
        """
        alerts_created = []
        days_remaining = calculate_days_remaining(product)

        # ── EMERGENCY_STOCK ──────────────────────────────────────────────────
        if is_emergency_stock(product) and product.emergency_reserve > 0:
            alert = await self._create_if_new(
                product=product,
                alert_type=AlertType.EMERGENCY_STOCK,
                days_remaining=days_remaining,
                threshold=product.emergency_reserve,
                severity=AlertSeverity.CRITICAL,
                message=(
                    f"EMERGENCY: {product.product_name} stock ({product.current_quantity} {product.unit}) "
                    f"has fallen to or below the emergency reserve of {product.emergency_reserve} {product.unit}. "
                    "Immediate procurement required."
                ),
            )
            if alert:
                alerts_created.append(alert)

        # ── OUT_OF_STOCK ─────────────────────────────────────────────────────
        if product.current_quantity <= 0:
            alert = await self._create_if_new(
                product=product,
                alert_type=AlertType.OUT_OF_STOCK,
                days_remaining=0.0,
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                message=(
                    f"{product.product_name} is OUT OF STOCK. "
                    f"Average daily usage: {product.average_daily_usage} {product.unit}/day."
                ),
            )
            if alert:
                alerts_created.append(alert)
            return alerts_created  # No point checking further

        # ── CRITICAL_STOCK ───────────────────────────────────────────────────
        if days_remaining is not None and days_remaining <= product.critical_days:
            alert = await self._create_if_new(
                product=product,
                alert_type=AlertType.CRITICAL_STOCK,
                days_remaining=days_remaining,
                threshold=float(product.critical_days),
                severity=AlertSeverity.CRITICAL,
                message=(
                    f"CRITICAL: {product.product_name} has only {days_remaining:.1f} days of stock remaining "
                    f"(current: {product.current_quantity} {product.unit}, "
                    f"daily usage: {product.average_daily_usage} {product.unit}/day, "
                    f"critical threshold: {product.critical_days} days)."
                ),
            )
            if alert:
                alerts_created.append(alert)

        # ── LOW_STOCK ─────────────────────────────────────────────────────────
        elif days_remaining is not None and days_remaining <= product.alert_days:
            alert = await self._create_if_new(
                product=product,
                alert_type=AlertType.LOW_STOCK,
                days_remaining=days_remaining,
                threshold=float(product.alert_days),
                severity=AlertSeverity.HIGH,
                message=(
                    f"LOW STOCK: {product.product_name} has {days_remaining:.1f} days of stock remaining "
                    f"(current: {product.current_quantity} {product.unit}, "
                    f"daily usage: {product.average_daily_usage} {product.unit}/day, "
                    f"alert threshold: {product.alert_days} days)."
                ),
            )
            if alert:
                alerts_created.append(alert)

        return alerts_created

    async def _create_if_new(
        self,
        product: Product,
        alert_type: AlertType,
        days_remaining: Optional[float],
        threshold: Optional[float],
        severity: AlertSeverity,
        message: str,
    ) -> Optional[Alert]:
        """Only create an alert if no active alert of this type exists for this product."""
        if await self.repo.has_active_alert(product.id, alert_type):
            logger.debug(
                "Skipping duplicate alert %s for product %s", alert_type, product.product_name
            )
            return None

        alert = Alert(
            product_id=product.id,
            alert_type=alert_type,
            current_stock=product.current_quantity,
            daily_usage=product.average_daily_usage,
            days_remaining=days_remaining,
            threshold=threshold,
            severity=severity,
            message=message,
            status=AlertStatus.ACTIVE,
        )
        alert = await self.repo.create(alert)
        logger.info(
            "Created %s alert (severity=%s) for product %s",
            alert_type, severity, product.product_name,
        )
        return alert

    async def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        from datetime import datetime, timezone
        alert = await self.repo.get_by_id(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        return await self.repo.update(alert)

    async def dismiss_alert(self, alert_id: int) -> Optional[Alert]:
        from datetime import datetime, timezone
        alert = await self.repo.get_by_id(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.DISMISSED
        alert.resolved_at = datetime.now(timezone.utc)
        return await self.repo.update(alert)

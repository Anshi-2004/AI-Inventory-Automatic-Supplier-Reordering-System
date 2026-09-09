from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus, AlertType


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, alert: Alert) -> Alert:
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: int) -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Alert], int]:
        count_r = await self.db.execute(select(func.count()).select_from(Alert))
        total = count_r.scalar_one()
        result = await self.db.execute(
            select(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_active(self) -> list[Alert]:
        result = await self.db.execute(
            select(Alert)
            .where(Alert.status == AlertStatus.ACTIVE)
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def has_active_alert(self, product_id: int, alert_type: AlertType) -> bool:
        """Check if an unresolved alert of the same type already exists (dedup)."""
        result = await self.db.execute(
            select(Alert).where(
                and_(
                    Alert.product_id == product_id,
                    Alert.alert_type == alert_type,
                    Alert.status == AlertStatus.ACTIVE,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def update(self, alert: Alert) -> Alert:
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

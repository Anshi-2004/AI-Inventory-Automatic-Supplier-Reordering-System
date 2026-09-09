from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_log import EmailLog, EmailStatus


class EmailLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, log: EmailLog) -> EmailLog:
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def get_by_id(self, log_id: int) -> Optional[EmailLog]:
        result = await self.db.execute(select(EmailLog).where(EmailLog.id == log_id))
        return result.scalar_one_or_none()

    async def get_by_purchase_order(self, order_id: int) -> list[EmailLog]:
        result = await self.db.execute(
            select(EmailLog)
            .where(EmailLog.purchase_order_id == order_id)
            .order_by(desc(EmailLog.created_at))
        )
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[list[EmailLog], int]:
        all_r = await self.db.execute(select(EmailLog))
        total = len(list(all_r.scalars().all()))
        result = await self.db.execute(
            select(EmailLog).order_by(desc(EmailLog.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_sent_count(self) -> int:
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.status == EmailStatus.SENT)
        )
        return len(list(result.scalars().all()))

    async def get_draft_count(self) -> int:
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.status.in_([EmailStatus.DRAFT, EmailStatus.APPROVED]))
        )
        return len(list(result.scalars().all()))

    async def update(self, log: EmailLog) -> EmailLog:
        await self.db.flush()
        await self.db.refresh(log)
        return log

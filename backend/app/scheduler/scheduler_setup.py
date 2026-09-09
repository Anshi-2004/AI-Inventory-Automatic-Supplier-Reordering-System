"""
APScheduler setup using AsyncIOScheduler.
The scheduler runs inside the same event loop as FastAPI.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config.settings import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def start_scheduler() -> None:
    from app.scheduler.jobs import inventory_check_job

    scheduler = get_scheduler()

    # Parse cron from settings (e.g. "0 6 * * *")
    cron_parts = settings.scheduler_cron.split()
    if len(cron_parts) == 5:
        minute, hour, day, month, day_of_week = cron_parts
        trigger = CronTrigger(
            minute=minute, hour=hour, day=day,
            month=month, day_of_week=day_of_week, timezone="UTC"
        )
    else:
        logger.warning("Invalid SCHEDULER_CRON '%s', defaulting to daily 6 AM UTC.", settings.scheduler_cron)
        trigger = CronTrigger(hour=6, minute=0, timezone="UTC")

    scheduler.add_job(
        inventory_check_job,
        trigger=trigger,
        id="inventory_check",
        name="Daily Inventory Check",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace window
    )

    scheduler.start()
    logger.info("Scheduler started. Inventory check cron: %s", settings.scheduler_cron)


def stop_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")

"""
APScheduler job definitions.
Each job wraps the business service to allow independent testing.
"""
import logging

logger = logging.getLogger(__name__)


async def inventory_check_job() -> None:
    """
    Scheduled job: runs the full inventory check.
    Calls inventory_monitor_service which manages its own DB session.
    """
    logger.info("=== Scheduled inventory check starting ===")
    try:
        from app.services.inventory_monitor_service import run_inventory_check
        summary = await run_inventory_check()
        logger.info(
            "=== Inventory check complete: %d products, %d alerts, %d orders ===",
            summary.get("products_checked", 0),
            summary.get("alerts_created", 0),
            summary.get("orders_created", 0),
        )
    except Exception as exc:
        logger.error("Scheduled inventory check FAILED: %s", exc, exc_info=True)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.alert import Alert
from app.models.product import Product
from app.models.user import User
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertListResponse, AlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


async def _enrich_alert(alert: Alert, db: AsyncSession) -> dict:
    result = await db.execute(select(Product).where(Product.id == alert.product_id))
    product = result.scalar_one_or_none()
    return {
        "id": alert.id,
        "product_id": alert.product_id,
        "product_name": product.product_name if product else None,
        "alert_type": alert.alert_type,
        "current_stock": alert.current_stock,
        "daily_usage": alert.daily_usage,
        "days_remaining": alert.days_remaining,
        "threshold": alert.threshold,
        "severity": alert.severity,
        "message": alert.message,
        "status": alert.status,
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at,
    }


@router.get("", response_model=AlertListResponse, summary="List all alerts")
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AlertRepository(db)
    items, total = await repo.get_all(skip=skip, limit=limit)
    enriched = [await _enrich_alert(a, db) for a in items]
    return AlertListResponse(items=enriched, total=total)


@router.get("/active", response_model=list[AlertResponse], summary="Get all active alerts")
async def get_active_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AlertRepository(db)
    alerts = await repo.get_active()
    return [await _enrich_alert(a, db) for a in alerts]


@router.post("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve an alert")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(db)
    alert = await service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return await _enrich_alert(alert, db)


@router.post("/{alert_id}/dismiss", response_model=AlertResponse, summary="Dismiss an alert")
async def dismiss_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(db)
    alert = await service.dismiss_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return await _enrich_alert(alert, db)

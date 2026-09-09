"""
Email routes: approve, send, retry, and view logs.
Human-in-the-loop: admin must approve before sending.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.email.email_service import EmailMessage
from app.email.smtp_service import get_smtp_service
from app.models.email_log import EmailStatus
from app.models.purchase_order import PurchaseOrderStatus
from app.models.user import User
from app.repositories.email_log_repo import EmailLogRepository
from app.repositories.purchase_order_repo import PurchaseOrderRepository
from app.schemas.email_log import EmailApproveRequest, EmailLogListResponse, EmailLogResponse

router = APIRouter(prefix="/email", tags=["Email"])


@router.get("/logs", response_model=EmailLogListResponse, summary="List all email logs")
async def list_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = EmailLogRepository(db)
    items, total = await repo.get_all(skip=skip, limit=limit)
    return EmailLogListResponse(items=items, total=total)


@router.get("/logs/{log_id}", response_model=EmailLogResponse, summary="Get email log by ID")
async def get_email_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = EmailLogRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    return log


@router.post("/logs/{log_id}/approve", response_model=EmailLogResponse,
             summary="Approve email draft (with optional edit) — Admin only")
async def approve_email(
    log_id: int,
    data: EmailApproveRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Human review step: admin can edit subject/body and mark as APPROVED.
    Does NOT send the email. Email is only sent via /email/send.
    Also accepts FAILED emails so the admin can reset and retry manually.
    """
    repo = EmailLogRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    if log.status == EmailStatus.SENT:
        raise HTTPException(status_code=400, detail="Email already sent")

    # Allow admin to edit before approving
    if data.subject is not None:
        log.subject = data.subject
    if data.body is not None:
        log.body = data.body

    # Reset error message when re-approving a failed email
    if log.status == EmailStatus.FAILED:
        log.error_message = None

    log.status = EmailStatus.APPROVED
    log = await repo.update(log)
    return log


@router.post("/send/{log_id}", response_model=EmailLogResponse,
             summary="Send an approved email — Admin only")
async def send_email(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Send an approved email via SMTP.
    Updates email_log status to SENT or FAILED.
    Updates purchase order status to EMAIL_SENT.
    """
    repo = EmailLogRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    if log.status != EmailStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Email must be APPROVED before sending. Current status: {log.status.value}",
        )

    email_svc = get_smtp_service()
    if not email_svc.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_FROM in your .env file.",
        )

    message = EmailMessage(
        recipient=log.recipient_email,
        subject=log.subject,
        body=log.body,
    )

    try:
        await email_svc.send_email(message)
        log.status = EmailStatus.SENT
        log.sent_at = datetime.now(timezone.utc)
        log.error_message = None

        # Update purchase order status
        if log.purchase_order_id:
            order_repo = PurchaseOrderRepository(db)
            order = await order_repo.get_by_id(log.purchase_order_id)
            if order:
                order.status = PurchaseOrderStatus.EMAIL_SENT
                await order_repo.update(order)

    except Exception as exc:
        log.status = EmailStatus.FAILED
        log.error_message = str(exc)

    log = await repo.update(log)
    return log


@router.post("/retry/{log_id}", response_model=EmailLogResponse,
             summary="Retry sending a failed email — Admin only")
async def retry_email(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retry sending a FAILED email without regenerating a new draft.
    Resets status then immediately attempts SMTP delivery.
    Updates status to SENT on success, or back to FAILED (with new error) on failure.
    """
    repo = EmailLogRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    if log.status == EmailStatus.SENT:
        raise HTTPException(status_code=400, detail="Email already sent successfully.")
    if log.status not in (EmailStatus.FAILED, EmailStatus.APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"Only FAILED or APPROVED emails can be retried. Current status: {log.status.value}",
        )

    email_svc = get_smtp_service()
    if not email_svc.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_FROM in your .env file.",
        )

    message = EmailMessage(
        recipient=log.recipient_email,
        subject=log.subject,
        body=log.body,
    )

    try:
        await email_svc.send_email(message)
        log.status = EmailStatus.SENT
        log.sent_at = datetime.now(timezone.utc)
        log.error_message = None

        # Update purchase order status
        if log.purchase_order_id:
            order_repo = PurchaseOrderRepository(db)
            order = await order_repo.get_by_id(log.purchase_order_id)
            if order:
                order.status = PurchaseOrderStatus.EMAIL_SENT
                await order_repo.update(order)

    except Exception as exc:
        log.status = EmailStatus.FAILED
        log.error_message = str(exc)

    log = await repo.update(log)
    return log

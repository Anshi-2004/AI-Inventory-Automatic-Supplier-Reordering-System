"""
AI email generation routes.
Human-in-the-loop: email is created as DRAFT, never auto-sent.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.email_log import EmailLog, EmailStatus
from app.models.purchase_order import PurchaseOrderStatus
from app.models.user import User
from app.repositories.email_log_repo import EmailLogRepository
from app.repositories.purchase_order_repo import PurchaseOrderRepository
from app.schemas.ai_email import GenerateEmailRequest, GenerateEmailResponse, RegenerateEmailRequest
from app.services.inventory_service import calculate_days_remaining
from app.services.reorder_calc_service import calculate_reorder_quantity

router = APIRouter(prefix="/ai", tags=["AI Email"])


async def _build_email_context(order_id: int, db: AsyncSession):
    """Build the InventoryEmailContext from database — never from LLM."""
    from app.ai.ai_service import InventoryEmailContext
    from app.repositories.product_repo import ProductRepository
    from app.repositories.supplier_repo import SupplierRepository

    order_repo = PurchaseOrderRepository(db)
    order = await order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not order.items:
        raise HTTPException(status_code=400, detail="Purchase order has no items")

    supplier_repo = SupplierRepository(db)
    supplier = await supplier_repo.get_by_id(order.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Use first item (main product) for email context
    primary_item = order.items[0]
    product = primary_item.product
    if not product:
        from app.repositories.product_repo import ProductRepository
        product_repo = ProductRepository(db)
        product = await product_repo.get_by_id(primary_item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    days_remaining = calculate_days_remaining(product)

    # Get supplier-product link for delivery days
    sp_list = await supplier_repo.get_supplier_products_for_product(product.id)
    sp = next((s for s in sp_list if s.supplier_id == supplier.id), None)
    delivery_days = sp.delivery_days if sp else supplier.average_delivery_days

    return InventoryEmailContext(
        product_name=product.product_name,
        product_code=product.product_code,
        current_stock=product.current_quantity,
        unit=product.unit,
        average_daily_usage=product.average_daily_usage,
        days_remaining=days_remaining or 0.0,
        requested_quantity=primary_item.requested_quantity,
        supplier_name=supplier.supplier_name,
        supplier_company=supplier.company_name,
        required_delivery_days=delivery_days,
        priority=order.priority.value,
    ), supplier, order


@router.post("/generate-email", response_model=GenerateEmailResponse,
             summary="Generate AI supplier email for a purchase order")
async def generate_email(
    data: GenerateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a professional supplier email using LangChain + OpenRouter.
    Saves as DRAFT in email_logs. Does NOT send automatically.
    """
    try:
        from app.ai.ai_service import get_ai_service
        ai = get_ai_service()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    context, supplier, order = await _build_email_context(data.purchase_order_id, db)

    try:
        draft = await ai.generate_supplier_email(context)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Save as DRAFT (not APPROVED, not SENT)
    email_repo = EmailLogRepository(db)
    log = EmailLog(
        purchase_order_id=order.id,
        supplier_id=supplier.id,
        recipient_email=supplier.email,
        subject=draft.subject,
        body=draft.body,
        status=EmailStatus.DRAFT,
        generated_by=current_user.id,
    )
    log = await email_repo.create(log)

    # Update order status
    order_repo = PurchaseOrderRepository(db)
    order.status = PurchaseOrderStatus.EMAIL_GENERATED
    await order_repo.update(order)

    return GenerateEmailResponse(
        email_log_id=log.id,
        purchase_order_id=order.id,
        subject=log.subject,
        body=log.body,
        recipient_email=log.recipient_email,
        status=log.status.value,
    )


@router.post("/regenerate-email", response_model=GenerateEmailResponse,
             summary="Regenerate AI email (creates new draft)")
async def regenerate_email(
    data: RegenerateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate a new email draft for the same purchase order.
    Old draft is NOT deleted (kept for audit). New draft created as DRAFT.
    """
    email_repo = EmailLogRepository(db)
    old_log = await email_repo.get_by_id(data.email_log_id)
    if not old_log:
        raise HTTPException(status_code=404, detail="Email log not found")
    if old_log.status == EmailStatus.SENT:
        raise HTTPException(status_code=400, detail="Cannot regenerate an already-sent email")

    try:
        from app.ai.ai_service import get_ai_service
        ai = get_ai_service()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    context, supplier, order = await _build_email_context(old_log.purchase_order_id, db)

    try:
        draft = await ai.generate_supplier_email(context)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    new_log = EmailLog(
        purchase_order_id=old_log.purchase_order_id,
        supplier_id=old_log.supplier_id,
        recipient_email=old_log.recipient_email,
        subject=draft.subject,
        body=draft.body,
        status=EmailStatus.DRAFT,
        generated_by=current_user.id,
    )
    new_log = await email_repo.create(new_log)

    return GenerateEmailResponse(
        email_log_id=new_log.id,
        purchase_order_id=order.id,
        subject=new_log.subject,
        body=new_log.body,
        recipient_email=new_log.recipient_email,
        status=new_log.status.value,
    )

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from . import activity_service, email_service, invoice_service, notification_service

GST_RATE = Decimal("0.18")


def generate_invoice_number() -> str:
    now = datetime.now(timezone.utc)
    return f"INV-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def generate_transaction_id() -> str:
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def make_payment(
    subscription_id: int,
    current_user: models.User,
    db: Session,
    payment_status: str = "success",
    ip_address: str | None = None,
):
    subscription = db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id,
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can make subscription payments")
    if subscription.status != "pending" and db.query(models.Payment).filter(
        models.Payment.subscription_id == subscription.id,
        models.Payment.payment_status == "success",
    ).first():
        raise HTTPException(status_code=409, detail="This subscription has already been paid")
    if payment_status not in ("success", "failed"):
        raise HTTPException(status_code=400, detail="payment_status must be success or failed")

    base_amount = Decimal(subscription.plan.price or 0)
    total_amount = (base_amount * (Decimal("1.00") + GST_RATE)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    now = datetime.now(timezone.utc)
    payment = models.Payment(
        subscription_id=subscription.id,
        amount=total_amount,
        payment_method="card",
        payment_status=payment_status,
        transaction_id=generate_transaction_id(),
        invoice_number=generate_invoice_number(),
        paid_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type=f"payment_{payment_status}",
        action_detail=f"Payment {payment.invoice_number} {payment_status} for subscription {subscription.id}",
        ip_address=ip_address,
    )
    db.flush()

    if payment_status == "success":
        subscription.status = "active"
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=subscription.plan.duration_days)
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Payment Successful",
            message=f"Payment of Rs. {payment.amount} succeeded for {subscription.plan.name}.",
            notification_type="payment_success",
            link="/student/payments/",
        )
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Subscription Activated",
            message=f"Your {subscription.plan.name} plan is active until {subscription.end_date.date()}.",
            notification_type="subscription_activated",
            link="/student/subscription/",
        )
        notification_service.NotificationService.notify_admins(
            db=db,
            title="Payment Received",
            message=f"{current_user.name} paid Rs. {payment.amount} for {subscription.plan.name} ({payment.invoice_number}).",
            notification_type="payment_success",
            link="/payments/",
        )
    else:
        subscription.status = "pending"
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Payment Failed",
            message=f"Payment for {subscription.plan.name} could not be completed.",
            notification_type="payment_failed",
            link="/student/plans/",
        )
        notification_service.NotificationService.notify_admins(
            db=db,
            title="Payment Failed",
            message=f"{current_user.name}'s payment for {subscription.plan.name} failed.",
            notification_type="payment_failed",
            link="/payments/",
        )

    db.commit()
    db.refresh(payment)
    if payment_status == "success":
        invoice_pdf = invoice_service.build_invoice_pdf(payment)
        email_service.send_email(
            to_email=current_user.email,
            subject=f"Invoice {payment.invoice_number} for your subscription",
            body=(
                f"Hello {current_user.name},\n\n"
                f"Your payment for the {subscription.plan.name} plan was successful.\n"
                f"Invoice Number: {payment.invoice_number}\n"
                f"Transaction ID: {payment.transaction_id}\n"
                f"Amount Paid: Rs. {payment.amount}\n\n"
                "Your invoice PDF is attached.\n\n"
                "Thank you for learning with AKR LMS."
            ),
            attachments=[(f"{payment.invoice_number}.pdf", invoice_pdf, "application/pdf")],
        )
    return payment


def payment_history(current_user: models.User, db: Session):
    return (
        db.query(models.Payment)
        .join(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id)
        .order_by(models.Payment.paid_at.desc())
        .all()
    )

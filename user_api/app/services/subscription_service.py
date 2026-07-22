from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from . import activity_service, notification_service


def has_active_subscription(
    db: Session,
    user_id: int,
) -> bool:

    subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active",
        )
        .first()
    )

    if subscription is None:
        return False

    if subscription.end_date < datetime.now(timezone.utc):
        subscription.status = "expired"
        notification_service.create_notification(
            db=db,
            user_id=user_id,
            title="Subscription Expired",
            message=f"Your {subscription.plan.name} subscription has expired.",
            notification_type="subscription_expired",
            link="/student/plans/",
        )
        db.commit()
        return False

    return True


def _notification_exists(db: Session, user_id: int, notification_type: str, message: str) -> bool:
    return (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == user_id,
            models.Notification.notification_type == notification_type,
            models.Notification.message == message,
        )
        .first()
        is not None
    )


def notify_subscription_status(db: Session, current_user: models.User) -> None:
    now = datetime.now(timezone.utc)
    active_subscriptions = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id, models.Subscription.status == "active")
        .all()
    )
    changed = False
    for subscription in active_subscriptions:
        if subscription.end_date < now:
            subscription.status = "expired"
            message = f"Your {subscription.plan.name} subscription has expired."
            if not _notification_exists(db, current_user.id, "subscription_expired", message):
                notification_service.create_notification(
                    db=db,
                    user_id=current_user.id,
                    title="Subscription Expired",
                    message=message,
                    notification_type="subscription_expired",
                    link="/student/plans/",
                )
            changed = True
            continue

        days_left = (subscription.end_date.date() - now.date()).days
        if 0 <= days_left <= 7:
            message = f"Your {subscription.plan.name} subscription expires in {days_left} day(s)."
            if not _notification_exists(db, current_user.id, "subscription_expiring", message):
                notification_service.create_notification(
                    db=db,
                    user_id=current_user.id,
                    title="Subscription Expiring Soon",
                    message=message,
                    notification_type="subscription_expiring",
                    link="/student/subscription/",
                )
                changed = True
    if changed:
        db.commit()


def create_subscription(
    db: Session,
    current_user: models.User,
    plan_id: int,
    ip_address: str | None = None,
):

    # Only students can purchase subscriptions
    if current_user.role.lower() != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can purchase subscriptions.",
        )

    # Get active plan
    plan = (
        db.query(models.Plan)
        .filter(
            models.Plan.id == plan_id,
            models.Plan.is_active == True,
        )
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found",
        )

    # Prevent duplicate active subscriptions
    if has_active_subscription(
        db,
        current_user.id,
    ):
        raise HTTPException(
            status_code=400,
            detail="You already have an active subscription.",
        )

    pending = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id,
        models.Subscription.status == "pending",
    ).first()
    if pending:
        raise HTTPException(
            status_code=409,
            detail="Complete or cancel your pending subscription payment first.",
        )

    now = datetime.now(timezone.utc)

    subscription = models.Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        start_date=now,
        end_date=now + timedelta(days=plan.duration_days),
        status="pending",
        auto_renew=False,
    )

    db.add(subscription)
    db.flush()
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="subscription_requested",
        action_detail=f"Requested subscription to plan {plan.name}",
        ip_address=ip_address,
    )
    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Subscription Awaiting Payment",
        message=f"Your {plan.name} subscription request was created. Complete payment to activate access.",
        notification_type="subscription_requested",
        link="/student/subscription/",
    )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="New Subscription Request",
        message=f"{current_user.name} requested the {plan.name} plan.",
        notification_type="subscription_requested",
        link="/subscriptions/",
    )
    db.commit()
    db.refresh(subscription)

    return subscription


def renew_subscription(
    db: Session,
    current_user: models.User,
    subscription_id: int,
    ip_address: str | None = None,
):
    subscription = (
        db.query(models.Subscription)
        .filter(models.Subscription.id == subscription_id, models.Subscription.user_id == current_user.id)
        .first()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can renew subscriptions")
    existing_pending = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id,
        models.Subscription.plan_id == subscription.plan_id,
        models.Subscription.status == "pending",
    ).first()
    if existing_pending:
        raise HTTPException(status_code=409, detail="A renewal payment is already pending")

    now = datetime.now(timezone.utc)
    renewal = models.Subscription(
        user_id=current_user.id,
        plan_id=subscription.plan_id,
        start_date=now,
        end_date=now + timedelta(days=subscription.plan.duration_days),
        status="pending",
        auto_renew=subscription.auto_renew,
    )
    db.add(renewal)
    db.flush()
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="subscription_renewed",
        action_detail=f"Requested renewal for plan {subscription.plan.name}",
        ip_address=ip_address,
    )
    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Renewal Awaiting Payment",
        message=f"Complete payment to renew your {subscription.plan.name} plan.",
        notification_type="subscription_requested",
        link="/student/subscription/",
    )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="Subscription Renewal Requested",
        message=f"{current_user.name} requested renewal of the {subscription.plan.name} plan.",
        notification_type="subscription_requested",
        link="/subscriptions/",
    )
    db.commit()
    db.refresh(renewal)
    return renewal

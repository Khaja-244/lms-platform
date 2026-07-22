from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, subscription_service

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)

legacy_router = APIRouter(tags=["Subscriptions"])


@router.post(
    "/subscribe/{plan_id}",
    response_model=schemas.SubscriptionOut,
)
def subscribe(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return subscription_service.create_subscription(
        db=db,
        current_user=current_user,
        plan_id=plan_id,
        ip_address=activity_service.get_client_ip(request),
    )


@router.get(
    "/me",
    response_model=list[schemas.SubscriptionOut],
)
def my_subscriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    subscription_service.notify_subscription_status(
        db=db,
        current_user=current_user,
    )
    return (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id)
        .all()
    )


@legacy_router.post(
    "/subscribe/",
    response_model=schemas.SubscriptionOut,
)
def subscribe_legacy(
    payload: schemas.SubscribeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return subscription_service.create_subscription(
        db=db,
        current_user=current_user,
        plan_id=payload.plan_id,
        ip_address=activity_service.get_client_ip(request),
    )


@router.post(
    "/renew/{subscription_id}",
    response_model=schemas.SubscriptionOut,
)
def renew_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return subscription_service.renew_subscription(
        db,
        current_user,
        subscription_id,
        ip_address=activity_service.get_client_ip(request),
    )

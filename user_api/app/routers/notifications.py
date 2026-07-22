from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def _owned(db, user_id, notification_id):
    item = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.user_id == user_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item


@router.get("/", response_model=list[schemas.NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@router.post("/mark-read/")
def mark_notifications_read(
    payload: schemas.MarkNotificationReadRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if payload.notification_ids:
        query = query.filter(models.Notification.id.in_(payload.notification_ids))
    updated = query.update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"updated": updated, "message": "Notifications marked as read"}


@router.post("/mark-all-read/")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    updated = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(False))
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"updated": updated, "message": "All notifications marked as read"}

@router.get("/item/{notification_id}", response_model=schemas.NotificationOut)
def detail(notification_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return _owned(db, current_user.id, notification_id)

@router.patch("/{notification_id}/read", response_model=schemas.NotificationOut)
def set_read(notification_id: int, is_read: bool = True, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    item = _owned(db, current_user.id, notification_id); item.is_read = is_read
    db.commit(); db.refresh(item)
    return item

@router.delete("/actions/clear-read")
def clear_read(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    deleted = db.query(models.Notification).filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(True)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted, "message": "Read notifications cleared"}

@router.delete("/item/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(notification_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db.delete(_owned(db, current_user.id, notification_id)); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/broadcast/")
def broadcast_notification(
    payload: schemas.BroadcastNotificationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    created = NotificationService.broadcast(
        db=db,
        title=payload.title,
        message=payload.message,
        link=payload.link,
    )
    db.commit()
    return {"created": created, "message": "Broadcast notification created"}

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.post("/", response_model=schemas.ActivityLogOut, status_code=status.HTTP_201_CREATED)
def create_activity_log(
    payload: schemas.ActivityLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    activity = activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type=payload.action_type,
        action_detail=payload.action_detail,
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/", response_model=list[schemas.ActivityLogOut])
def my_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == current_user.id)
        .order_by(models.ActivityLog.created_at.desc())
        .all()
    )

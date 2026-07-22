from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, notification_service

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=schemas.UserOut)
def my_profile(
    current_user: models.User = Depends(auth.get_current_user),
):
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_profile(
    payload: schemas.ProfileUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    existing = (
        db.query(models.User)
        .filter(models.User.email.ilike(payload.email.strip()), models.User.id != current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email is already used by another account")

    current_user.name = payload.name.strip()
    current_user.email = payload.email.strip().lower()
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="profile_update",
        action_detail="Student updated profile details.",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    payload: schemas.PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = auth.hash_password(payload.new_password)
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="password_change",
        action_detail="Student changed account password.",
        ip_address=activity_service.get_client_ip(request),
    )
    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Password Changed",
        message="Your account password was changed successfully.",
        notification_type="password_changed",
        link="/student/profile/",
    )
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/profile-picture", response_model=schemas.UserOut)
def update_profile_picture(
    payload: schemas.ProfilePictureRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    current_user.profile_picture = payload.profile_picture
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="profile_picture_update",
        action_detail="Student updated profile picture.",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    db.refresh(current_user)
    return current_user

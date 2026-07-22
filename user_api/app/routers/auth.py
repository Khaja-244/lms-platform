"""
app/routers/auth.py

Authentication endpoints
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, notification_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

legacy_router = APIRouter(tags=["Authentication"])


# ==========================================================
# Register
# ==========================================================
@router.post(
    "/register/",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: schemas.RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Check if email already exists
    existing = (
        db.query(models.User)
        .filter(
            models.User.email.ilike(payload.email.strip())
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )

    # Create new user
    user = models.User(
        name=payload.name,
        email=str(payload.email).lower(),
        role="student",
        password_hash=auth.hash_password(
            payload.password.strip()
        ),

        # Django fields
        is_active=True,
        is_staff=False,
        is_superuser=False,

        # Explicitly set timestamp instead of relying on DB default
        date_joined=datetime.now(timezone.utc),
    )

    db.add(user)
    db.flush()
    notification_service.create_notification(
        db=db,
        user_id=user.id,
        title="Welcome to Video Learning",
        message="Your account has been created successfully.",
        notification_type="welcome_registration",
        link="/student/courses/",
    )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="New Student Registration",
        message=f"{user.name} ({user.email}) registered as a student.",
        notification_type="new_registration",
        link="/accounts/users/",
    )
    activity_service.log_activity(
        db=db,
        user_id=user.id,
        action_type="welcome_registration",
        action_detail="User registered through FastAPI.",
        ip_address=activity_service.get_client_ip(request),
    )
    notification_service.create_notification(
        db=db,
        user_id=user.id,
        title="New Login",
        message="A successful login was recorded for your account.",
        notification_type="login",
        link=(
            "/student/profile/" if user.role == "student"
            else "/instructor/dashboard/" if user.role == "instructor"
            else "/analytics/"
        ),
    )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="User Login",
        message=f"{user.name} ({user.email}) logged in as {user.role}.",
        notification_type="login",
        link="/analytics/",
    )
    db.commit()
    db.refresh(user)

    return user


# ==========================================================
# Login
# ==========================================================
@router.post(
    "/login/",
    response_model=schemas.TokenResponse,
)
def login(
    payload: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(
            models.User.email.ilike(payload.email.strip())
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not auth.verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account has been deactivated",
        )

    access_token = auth.create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )
    activity_service.log_activity(
        db=db,
        user_id=user.id,
        action_type="login",
        action_detail="User logged in through FastAPI.",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserInfo(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            profile_picture=user.profile_picture or "",
        ),
    )


@router.post("/logout/")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="logout",
        action_detail="User logged out through FastAPI.",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    return {"message": "Logout logged successfully"}


@legacy_router.post("/register/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_legacy(
    payload: schemas.RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return register(payload=payload, request=request, db=db)


@legacy_router.post("/login/", response_model=schemas.TokenResponse)
def login_legacy(
    payload: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return login(payload=payload, request=request, db=db)

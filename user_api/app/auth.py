"""
app/auth.py
"""

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import get_db
from . import models

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

if os.getenv("APP_ENV", "development").lower() == "production" and SECRET_KEY in {
    "change-this-in-production",
    "dev-jwt-secret-change-in-production",
    "REPLACE_WITH_A_DIFFERENT_REAL_RANDOM_SECRET",
}:
    raise RuntimeError("Set JWT_SECRET_KEY to a strong secret before starting in production")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 720000

bearer_scheme = HTTPBearer()


# ==========================================================
# Password Hashing
# ==========================================================

def _pbkdf2_encode(
    password: str,
    salt: str,
    iterations: int,
) -> str:

    dk = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode(),
        salt.encode(),
        iterations,
    )

    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}"
        f"${iterations}"
        f"${salt}"
        f"${base64.b64encode(dk).decode()}"
    )


def hash_password(password: str) -> str:

    salt = secrets.token_hex(11)

    return _pbkdf2_encode(
        password,
        salt,
        PBKDF2_ITERATIONS,
    )


def verify_password(
    plain_password: str,
    stored_password: str,
) -> bool:

    try:

        algorithm, iterations, salt, _ = stored_password.split(
            "$",
            3,
        )

        if algorithm != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False

        encoded = _pbkdf2_encode(
            plain_password,
            salt,
            int(iterations),
        )

        return secrets.compare_digest(
            encoded,
            stored_password,
        )

    except Exception:
        return False


# ==========================================================
# JWT
# ==========================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
):

    payload = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + (
        expires_delta
        or timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
):

    try:

        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

def get_user_from_token(
    token: str,
    db: Session,
) -> models.User:

    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    return user


# ==========================================================
# Current User
# ==========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    return get_user_from_token(
        token=credentials.credentials,
        db=db,
    )


# ==========================================================
# Instructor Guard
# ==========================================================

def require_instructor(
    current_user: models.User = Depends(
        get_current_user
    ),
):

    if current_user.role not in (
        "admin",
        "instructor",
    ):
        raise HTTPException(
            status_code=403,
            detail="Instructor role required",
        )

    return current_user


def require_admin(
    current_user: models.User = Depends(
        get_current_user
    ),
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required",
        )

    return current_user

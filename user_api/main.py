"""
main.py

Entrypoint for the FastAPI User Panel service.
Run with:
    uvicorn main:app --reload --port 8001

Interactive API docs (auto-generated):
    http://localhost:8001/docs
"""

import logging
import os
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import (
    auth,
    courses,
    enrollment,
    progress,
    plans,
    subscriptions,
    payments,
    notifications,
    activity,
    analytics,
    profile,
    chat,
    websocket,
    attendance,
    assignments,
)
from app.database import Base, engine
import app.models  # Ensure all SQLAlchemy models are registered

# Django migrations are the schema source of truth. Automatic SQLAlchemy DDL
# is opt-in only for isolated experiments and is disabled in Docker/production.
if os.getenv("FASTAPI_AUTO_CREATE_TABLES", "False").lower() == "true":
    Base.metadata.create_all(bind=engine)
load_dotenv()

# ---------------------------------------------------------------------------
# Logging - plain console logging, easy to redirect to a log aggregator
# in a real deployment without changing any application code.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("lms_user_api")

app = FastAPI(
    title="LMS User Panel API",
    description="REST API for learners and instructors. Shares a database with the Django Admin Panel.",
    version="1.0.0",
)

# CORS origins are configurable via env var (comma-separated), e.g.:
#   CORS_ORIGINS=https://admin.example.com,https://app.example.com
# Defaults to localhost origins for local development. Using "*" with
# allow_credentials=True is not spec-compliant CORS behavior, so we
# avoid it entirely rather than relying on browsers being lenient.
_cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auth.legacy_router)
app.include_router(courses.router)
app.include_router(enrollment.router)
app.include_router(progress.router)

app.include_router(plans.router)
app.include_router(subscriptions.router)
app.include_router(subscriptions.legacy_router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(activity.router)
app.include_router(analytics.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(websocket.router)
app.include_router(attendance.router)
app.include_router(assignments.router)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

@app.get("/", tags=["Health"])
def health_check():
    """Simple health check so you can confirm the service is up."""
    return {"status": "ok", "service": "LMS User Panel API"}


# ---------------------------------------------------------------------------
# Consistent, RESTful error responses (task spec: "proper error handling")
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    first_message = errors[0].get("msg", "Validation failed") if errors else "Validation failed"
    if first_message.lower().startswith("value error, "):
        first_message = first_message[13:]
    return JSONResponse(
        status_code=422,
        content={"error": True, "message": first_message, "details": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    """
    Safety net for anything not already caught above (a bug, a DB outage,
    etc.). Logs the full exception server-side for debugging, but never
    leaks internal details (stack traces, DB errors, file paths) to the
    client - that's a real information-disclosure risk in production.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error"},
    )

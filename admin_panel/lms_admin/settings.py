"""
Django settings for lms_admin project (Admin Panel).
Shares a PostgreSQL database with the FastAPI User Panel.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # loads DJANGO_*, POSTGRES_* variables from .env

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-this-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Fail loudly instead of silently deploying with an insecure default key.
# (Deliberately skipped during `manage.py check`/migrations in DEBUG mode
# so local dev and CI don't need a real secret key.)
if not DEBUG and SECRET_KEY in {
    "change-this-in-production",
    "REPLACE_WITH_A_REAL_RANDOM_SECRET",
    "replace-with-a-long-random-string",
}:
    raise RuntimeError(
        "DJANGO_SECRET_KEY is still set to the insecure default. "
        "Set a real, random value via the DJANGO_SECRET_KEY environment "
        "variable before running with DJANGO_DEBUG=False."
    )

# Extra hardening that only makes sense once you're not in local dev
# (DEBUG=True locally would otherwise force HTTPS-only cookies etc.,
# which breaks plain http://localhost testing).
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True") == "True"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# Needed when the Admin Panel sits behind a reverse proxy/load balancer
# that terminates TLS (Nginx, Render, Railway, etc.) - without this,
# Django thinks every request is plain HTTP and SECURE_SSL_REDIRECT loops.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# If you deploy behind a custom domain, list it here (comma-separated)
# so Django's CSRF protection trusts POSTs coming from it.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project Apps
    "accounts",
    "courses",
    "dashboard",
    "plans",
    "subscriptions",
    "payments",
    "analytics.apps.AnalyticsConfig",
    "student",
    "instructor",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files efficiently without Nginx
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lms_admin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "analytics.context_processors.notification_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "lms_admin.wsgi.application"

# ---------------------------------------------------------------------------
# Database (SHARED with FastAPI user_api service)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "lms_db"),
        "USER": os.environ.get("POSTGRES_USER", "lms_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "lms_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        # Reuses DB connections across requests instead of opening a new
        # one every time - meaningful under real traffic. 0 (default)
        # would be fine for low traffic too, but this avoids a common
        # "runs fine in dev, chokes under load" surprise.
        "CONN_MAX_AGE": int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", "60")),
    }
}

# Custom user model (id, name, email, role, password_hash equivalent)
AUTH_USER_MODEL = "accounts.User"

# IMPORTANT (Django <-> FastAPI integration):
# Both services must be able to verify the same password_hash values,
# since they share the `users` table. We deliberately keep Django's
# DEFAULT hasher (PBKDF2PasswordHasher) because its output format is
# stable and fully documented:
#     pbkdf2_sha256$<iterations>$<salt>$<base64-hash>
# The FastAPI service re-implements this exact algorithm by hand in
# user_api/app/auth.py (using Python's built-in hashlib, no external
# library guesswork) so a user registered in either service can log
# into the other one.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: compresses + fingerprints static files and serves them
# directly from the Django process, so you don't need a separate Nginx
# container just to serve CSS/JS in production.
#
# IMPORTANT: CompressedManifestStaticFilesStorage requires a manifest
# file that's only generated by `collectstatic`. We only switch to it
# when DEBUG=False (i.e. a real deploy, where you're expected to run
# collectstatic as part of your build step - see Dockerfile). In local
# dev (DEBUG=True), we keep Django's plain static storage so
# `python manage.py runserver` keeps working without any extra steps.
if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Auth redirects
# ---------------------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Console-based structured-ish logging. In a real deployment, point this
# at your log aggregator (CloudWatch, Datadog, etc.) by adding a handler -
# everything else (loggers/levels) stays the same.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.request": {
            # Always surface 500s, even if other Django logs are quieted down.
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Media Files (Course Images & Lesson Videos)
# ---------------------------------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

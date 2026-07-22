#!/bin/sh
# entrypoint.sh
#
# Same image, two modes, chosen by DJANGO_DEBUG:
#   DJANGO_DEBUG=True   -> Django's dev server (auto-reload, verbose errors)
#   DJANGO_DEBUG=False  -> gunicorn (production WSGI server, no auto-reload)
#
# Migrations are handled differently per mode, on purpose:
#   - DEV: apply the reviewed, committed migration files.
#   - PRODUCTION: we deliberately do NOT run `makemigrations` here.
#     Auto-generating migrations against a live database on every deploy
#     is a real anti-pattern - migrations should be generated once,
#     reviewed, committed to version control, and only `migrate` should
#     run at deploy time. See README "Before your first production deploy".

set -e

if [ "$DJANGO_DEBUG" = "False" ]; then
    echo "Starting in PRODUCTION mode (gunicorn)..."

    # Fail fast with a clear message instead of silently starting with
    # missing tables, if the one-time "generate + commit migrations"
    # step (see README) hasn't been done yet.
    if [ -z "$(ls -A accounts/migrations 2>/dev/null | grep -v __init__)" ]; then
        echo "ERROR: No migration files found in accounts/migrations/." >&2
        echo "Before your first production deploy, run this once and commit the result:" >&2
        echo "  python manage.py makemigrations accounts courses dashboard plans subscriptions payments" >&2
        echo "See README.md -> 'Running in production mode' for details." >&2
        exit 1
    fi

    echo "Applying pre-committed migrations..."
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    exec gunicorn lms_admin.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting in DEVELOPMENT mode (runserver)..."
    echo "Applying committed migrations..."
    python manage.py migrate --noinput
    exec python manage.py runserver 0.0.0.0:8000
fi

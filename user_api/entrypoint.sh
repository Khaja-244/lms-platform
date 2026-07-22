#!/bin/sh
# entrypoint.sh
#
# Same image, two modes, chosen by APP_ENV:
#   APP_ENV=development (default) -> uvicorn with --reload, single process
#   APP_ENV=production             -> gunicorn managing multiple uvicorn workers
#
# Always waits for Django's migrations to finish first (see wait_for_db.py).

set -e

echo "Waiting for the database to be ready..."
python wait_for_db.py

if [ "$APP_ENV" = "production" ]; then
    echo "Starting in PRODUCTION mode (gunicorn + uvicorn workers)..."
    exec gunicorn main:app \
        --bind 0.0.0.0:8001 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting in DEVELOPMENT mode (uvicorn --reload)..."
    exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload
fi

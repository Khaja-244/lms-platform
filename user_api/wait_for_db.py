"""
wait_for_db.py

Docker-Compose starts both application containers concurrently. This script
waits for the required Django migrations, not merely database connectivity,
so SQLAlchemy can never race Django's schema owner.
"""

import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

POSTGRES_USER = os.getenv("POSTGRES_USER", "lms_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "lms_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "lms_db")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

MAX_WAIT_SECONDS = int(os.getenv("DB_MIGRATION_WAIT_SECONDS", "120"))
POLL_INTERVAL_SECONDS = 2
REQUIRED_MIGRATIONS = {
    ("accounts", "0002_user_profile_picture"),
    ("courses", "0005_attendance_assignment_submission"),
    ("analytics", "0003_chat_tables_and_state"),
}


def main():
    engine = create_engine(DATABASE_URL)
    waited = 0

    while waited < MAX_WAIT_SECONDS:
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT app, name FROM django_migrations")).fetchall()
            applied = {(row[0], row[1]) for row in rows}
            missing = REQUIRED_MIGRATIONS - applied
            if not missing:
                print("Database is ready - required Django migrations are applied.")
                return
            print(f"Waiting for required migrations: {sorted(missing)} ({waited}s)")
        except (OperationalError, ProgrammingError):
            print(f"Waiting for database/migrations... ({waited}s)")
        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    print("Timed out waiting for the database to be ready.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

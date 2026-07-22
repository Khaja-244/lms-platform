FROM python:3.12-slim

WORKDIR /app

# System deps needed to build psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Generates migration files (since none are pre-built in this repo),
# applies them, then starts either the dev server or gunicorn depending
# on DJANGO_DEBUG. See entrypoint.sh.
CMD ["./entrypoint.sh"]

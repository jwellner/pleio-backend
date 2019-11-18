#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Compile messages
python /app/manage.py compilemessages

# Run migrations
python /app/manage.py migrate

# Run migrations shared
python /app/manage.py migrate_schemas --shared

# Create initial revisions
python /app/manage.py createinitialrevisions

# Start Gunicorn processes
python manage.py runserver 0.0.0.0:8000
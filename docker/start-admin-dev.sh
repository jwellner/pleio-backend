#!/usr/bin/env bash

# Collect static
python manage.py collectstatic --noinput

# Run migrations shared on admin pod only
python /app/manage.py migrate_schemas

# Start Gunicorn processes
python manage.py runserver 0.0.0.0:8888
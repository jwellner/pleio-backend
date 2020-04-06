#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Start Gunicorn processes
python manage.py runserver 0.0.0.0:8000
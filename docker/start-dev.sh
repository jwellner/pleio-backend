#!/bin/bash

# Collect static
python /app/manage.py collectstatic --noinput

# Run migrations
python /app/manage.py migrate

# Create initial revisions
python /app/manage.py createinitialrevisions

# Start Gunicorn processes
python manage.py runserver 0.0.0.0:8000
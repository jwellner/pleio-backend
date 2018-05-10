#!/bin/bash

# Collect static
python /app/src/manage.py collectstatic --noinput

# Run migrations
python /app/src/manage.py migrate

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --http :8000 --chdir /app/src --module backend.wsgi --static-map /static=/app/static --static-map /media=/app/media

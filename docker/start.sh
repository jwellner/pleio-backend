#!/bin/bash

# Collect static
python /app/manage.py collectstatic --noinput

# Run migrations
python /app/manage.py migrate

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --http :8000 --module backend2.wsgi --static-map /static=/app/static --static-map /media=/app/media

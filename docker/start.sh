#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Run migrations shared
python /app/manage.py migrate_schemas

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --http :8000 --wsgi-disable-file-wrapper --module backend2.wsgi --static-map /static=/app/static

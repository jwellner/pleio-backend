#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Compile messages
python /app/manage.py compilemessages

# Run migrations shared
python /app/manage.py migrate_schemas

# Create initial revisions
python /app/manage.py createinitialrevisions

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --http :8000 --module backend2.wsgi --static-map /static=/app/static --static-map /media=/app/media

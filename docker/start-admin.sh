#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Run migrations shared on admin pod only
# python /app/manage.py migrate_schemas

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --ini /uwsgi-prod.ini
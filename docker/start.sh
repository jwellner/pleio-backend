#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --ini /uwsgi-prod.ini
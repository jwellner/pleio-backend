#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Start Gunicorn processes
echo Starting uwsgi
uwsgi --http :8000 --wsgi-disable-file-wrapper --module backend2.wsgi --static-map /static=/app/static --enable-threads

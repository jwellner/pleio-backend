#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Run migrations shared on admin pod only
python /app/manage.py migrate_schemas

# Start Gunicorn processes 
echo Starting uwsgi with python autoreload
uwsgi --http :8888 --wsgi-disable-file-wrapper --module backend2.wsgi --static-map /static=/app/static --enable-threads --python-autoreload 1

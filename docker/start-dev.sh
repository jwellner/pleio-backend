#!/usr/bin/env bash

# Collect static
python /app/manage.py collectstatic --noinput

# Gzip js and css
yes n | gzip -k static/**/*.{js,css}

# Start Gunicorn processes 
echo Starting uwsgi
uwsgi --ini /uwsgi-dev.ini
#!/usr/bin/env bash

# Collect static
python manage.py collectstatic --noinput

# Start Gunicorn processes
python manage.py runserver 0.0.0.0:8888
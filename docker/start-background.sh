#!/usr/bin/env bash

echo "[i] Starting celery..."
celery -A backend2.celery worker -B -E -O fair -s "/tmp/celerybeat-schedule" --loglevel=info

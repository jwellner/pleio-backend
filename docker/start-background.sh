#!/usr/bin/env bash

echo "[i] Starting celery..."
celery -B -A backend2 worker -l info -s "/tmp/celerybeat-schedule"

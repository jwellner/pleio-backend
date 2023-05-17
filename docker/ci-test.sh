#!/usr/bin/env bash

cd /app
python manage.py collectstatic --noinput
coverage run --source='/app/.' manage.py test "$@" --noinput \
    && coverage combine \
    && coverage report
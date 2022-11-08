#!/usr/bin/env bash

cd /app
python manage.py collectstatic --noinput
coverage run --data-file=/tmp/.coverage --source='/app/.' manage.py test --noinput && coverage report --data-file=/tmp/.coverage
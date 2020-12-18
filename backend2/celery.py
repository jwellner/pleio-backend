from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.utils.log import get_task_logger
from .crontab import beat_schedule

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend2.settings')

logger = get_task_logger(__name__)

app = Celery('backend2')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.logger = logger

app.conf.beat_schedule = beat_schedule
app.conf.result_backend = 'rpc://'
app.conf.result_persistent = False

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

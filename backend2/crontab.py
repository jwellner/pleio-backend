from celery.schedules import crontab

beat_schedule = {
    # The 'minute' definition can be used for testing purposes
    #'minute': {
    #    'task': 'core.tasks.dispatch_cron',
    #    'schedule': crontab(minute='*', hour='*'),
    #    'args': ['minute']
    #},
    'hourly': {
        'task': 'core.tasks.dispatch_crons',
        'schedule': crontab(minute=0, hour='*'),
        'args': ['hourly']
    },
    'daily': {
        'task': 'core.tasks.dispatch_crons',
        'schedule': crontab(minute=0, hour=21),
        'args': ['daily']
    },
    'weekly': {
        'task': 'core.tasks.dispatch_crons',
        'schedule': crontab(minute=0, hour=4, day_of_week='monday'),
        'args': ['weekly']
    },
    'monthly': {
        'task': 'core.tasks.dispatch_crons',
        'schedule': crontab(minute=0, hour=21, day_of_month=1),
        'args': ['monthly']
    },
    'yearly': {
        'task': 'core.tasks.dispatch_crons',
        'schedule': crontab(minute=0, hour=21, day_of_month=1, month_of_year=1),
        'args': ['yearly']
    },
    'file_scan': {
        'task': 'core.tasks.dispatch_task',
        'schedule': crontab(minute=15, hour=2),
        'args': ['file.tasks.scan']
    }
}
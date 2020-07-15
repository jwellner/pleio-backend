from celery.schedules import crontab

beat_schedule = {
    # The 'minute' definition can be used for testing purposes
    #'minute': {
    #    'task': 'background.dispatch_cron',
    #    'schedule': crontab(minute='*', hour='*'),
    #    'args': ['minute']
    #},
    'hourly': {
        'task': 'background.dispatch_cron',
        'schedule': crontab(minute=0, hour='*'),
        'args': ['hourly']
    },
    'daily': {
        'task': 'background.dispatch_cron',
        'schedule': crontab(minute=0, hour=21),
        'args': ['daily']
    },
    'weekly': {
        'task': 'background.dispatch_cron',
        'schedule': crontab(minute=0, hour=21, day_of_week='sunday'),
        'args': ['weekly']
    },
    'monthly': {
        'task': 'background.dispatch_cron',
        'schedule': crontab(minute=0, hour=21, day_of_month=1),
        'args': ['monthly']
    },
    'yearly': {
        'task': 'background.dispatch_cron',
        'schedule': crontab(minute=0, hour=21, day_of_month=1, month_of_year=1),
        'args': ['yearly']
    },
}
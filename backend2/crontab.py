from celery.schedules import crontab

beat_schedule = {
    # The 'minute' definition can be used for testing purposes
    #'minute': {
    #    'task': 'core.tasks.dispatch_hourly_cron',
    #    'schedule': crontab(minute='*', hour='*'),
    #    'args': ['minute']
    #},
    'hourly': {
        'task': 'core.tasks.cronjobs.dispatch_hourly_cron',
        'schedule': crontab(minute=55, hour='*'),
    },
    'daily': {
        'task': 'core.tasks.cronjobs.dispatch_daily_cron',
        'schedule': crontab(minute=0, hour=21),
    },
    'weekly': {
        'task': 'core.tasks.cronjobs.dispatch_weekly_cron',
        'schedule': crontab(minute=0, hour=4, day_of_week='monday'),
    },
    'monthly': {
        'task': 'core.tasks.cronjobs.dispatch_monthly_cron',
        'schedule': crontab(minute=0, hour=21, day_of_month=1),
    },
    'file_scan': {
        'task': 'core.tasks.cronjobs.dispatch_task',
        'schedule': crontab(minute=15, hour=23),
        'args': ['file.tasks.schedule_scan']
    },
    'control_poll_task': {
        'task': 'control.tasks.poll_task_result',
        'schedule': 10.0,
    },
}

import os

from django import template
from django.conf import settings

from control.lib import reverse
from control.models import Task

register = template.Library()


@register.simple_tag
def backup_url(task: Task):
    if task.state == 'SUCCESS' and task.response:
        backup_file = os.path.join(settings.BACKUP_PATH, task.response)
        if os.path.exists(backup_file) and os.path.isfile(backup_file):
            return reverse('download_backup', args=(task.id,))


@register.simple_tag
def if_without_files(task: Task, if_true_message, else_message=''):
    if task.arguments[1]:
        return if_true_message
    return else_message

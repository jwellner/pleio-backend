from django.core.management.base import BaseCommand
from celery.result import AsyncResult


class Command(BaseCommand):
    help = 'Show status of a celery task.'

    def add_arguments(self, parser):
        parser.add_argument('task_id', help='UUID style task-id')

    def handle(self, task_id, **options):
        task_result = AsyncResult(task_id)
        print(f"Task ID: {task_id}")
        print(f"Status: {task_result.status}")
        if task_result.ready():
            print(f"Done: {task_result.date_done}")
            print(f"Result: {task_result.result}")

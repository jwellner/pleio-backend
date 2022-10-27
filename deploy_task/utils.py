from django.core.management import BaseCommand
from django.utils.module_loading import import_string


class DeployCommandBase(BaseCommand):
    deploy_task = None

    def add_arguments(self, parser):
        parser.add_argument('--schema', default=None, help="Only one schema")
        parser.add_argument('--now', default=False, action='store_true', help="Execute directly")

    def handle(self, *args, **options):
        assert import_string(self.deploy_task), 'Provide a valid python library path to the deploy task.'

        if options['schema']:
            self.maybe_async_one(options['schema'], options['now'])
        else:
            self.maybe_async_all(options['now'])

    def maybe_async_all(self, now):
        from deploy_task.tasks import schedule_deploy_task_for_all
        if now:
            schedule_deploy_task_for_all(self.deploy_task)
        else:
            schedule_deploy_task_for_all.delay(self.deploy_task)

    def maybe_async_one(self, schema, now):
        from deploy_task.tasks import execute_deploy_task
        if now:
            execute_deploy_task(schema, self.deploy_task)
        else:
            execute_deploy_task.delay(schema, self.deploy_task)

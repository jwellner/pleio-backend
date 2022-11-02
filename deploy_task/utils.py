from django.core.management import BaseCommand
from django.utils.module_loading import import_string


class DeployCommandBase(BaseCommand):
    deploy_task = None

    def add_arguments(self, parser):
        parser.add_argument('--schema', default=None, help="Only one schema")
        parser.add_argument('--now', default=False, action='store_true', help="Execute directly")

    def handle(self, *args, **options):
        try:
            import_string(self.deploy_task_as_string())
        except Exception as e:
            self.stderr.write("%s: %s" %(e.__class__, str(e)))
            self.stderr.write("Provide a function with a valid python library path for the deploy task.")
            return

        if options['schema']:
            self.maybe_async_one(options['schema'], options['now'])
        else:
            self.maybe_async_all(options['now'])

    def deploy_task_as_string(self):
        if isinstance(self.deploy_task, str):
            return self.deploy_task
        return f"{self.deploy_task.__module__}.{self.deploy_task.__qualname__}"

    def maybe_async_all(self, now):
        from deploy_task.tasks import schedule_deploy_task_for_all
        if now:
            schedule_deploy_task_for_all(self.deploy_task_as_string())
        else:
            task = schedule_deploy_task_for_all.delay(self.deploy_task_as_string())
            self.stdout.write(task.id)

    def maybe_async_one(self, schema, now):
        from deploy_task.tasks import execute_deploy_task
        if now:
            execute_deploy_task(schema, self.deploy_task_as_string())
        else:
            task = execute_deploy_task.delay(schema, self.deploy_task_as_string())
            self.stdout.write(task.id)

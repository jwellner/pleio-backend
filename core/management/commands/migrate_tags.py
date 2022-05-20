from celery.result import AsyncResult
from django.core.management import BaseCommand
from tenants.models import Client


class Command(BaseCommand):
    help = 'Cleanup deleted users'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-r', '--revert', default=False, action='store_true', help="Undo the tag migration")
        parser.add_argument('--status')

    def handle(self, *args, **options):
        if options.get('status'):
            self.report_status(options['status'])
            return

        if not options['revert']:
            self.stdout.write(f"Migrate tags for all schema's. A list of task id's follows.")
            self.stdout.write(f"To recall the status, use the next line in your terminal:\n\n./manage.py migrate_tags --status ", ending='')
            self.migrate()
        else:
            self.stdout.write(f"Revert migration of tags for all schema's.")
            self.stdout.write(f"To recall the status, use the next line in your terminal:\n\n./manage.py migrate_tags --status ", ending='')
            self.revert()
        self.stdout.write("\n\n")

    def report_status(self, ids):
        from backend2.celery import app
        for line in ids.split(','):
            if line:
                schema, id = line.split(':')
                task = AsyncResult(id=id, app=app)
                self.stdout.write(f"{schema}: {task.status}")

    def migrate(self):
        from core.tasks import migrate_tags
        for client in Client.objects.exclude(name='public'):
            task_status = migrate_tags.delay(client.schema_name)
            self.stdout.write(f"{client.schema_name}:{task_status.id},", ending='')

    def revert(self):
        from core.tasks import revert_tags
        for client in Client.objects.exclude(name='public'):
            task_status = revert_tags.delay(client.schema_name)
            self.stdout.write(f"revert-{client.schema_name}:{task_status.id},", ending='')

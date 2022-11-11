from django_tenants.utils import schema_context
from post_deploy.management.commands.deploy import Command as DeployCommand

from tenants.models import Client


class Command(DeployCommand):
    def handle(self, *args, **options):
        for client in Client.objects.exclude(schema_name='public'):
            with schema_context(client.schema_name):
                self.stdout.write("Deployment at ['%s']" % client.schema_name)
                super().handle(*args, **options)

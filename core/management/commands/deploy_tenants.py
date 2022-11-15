from time import sleep

from django_tenants.utils import schema_context
from post_deploy.management.commands.deploy import Command as DeployCommand

from core import config
from core.lib import is_schema_public
from tenants.models import Client


class Command(DeployCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema', default=None)
        parser.add_argument('--sleep', type=int, default=100, help="Milliseconds rest after switch to the next schema.")

    def handle(self, *args, **options):
        if not is_schema_public():
            raise Exception("This command is not to be run with a tenant schema enabled.")

        clients = Client.objects.exclude(schema_name='public')
        if options.get('schema'):
            clients = clients.filter(schema_name=options.pop('schema'))

        waiting_time = options.pop('sleep')

        for client in clients:
            with schema_context(client.schema_name):
                # somehow the connection with the database is not always as expected at management commands.
                # until we know what is going on... sleep.
                sleep(waiting_time/1000)

                self.stdout.write("Deployment at %s (%s)" % (client.schema_name, config.NAME))
                super().handle(*args, **options)

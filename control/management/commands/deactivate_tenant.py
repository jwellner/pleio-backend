import os
import logging
from django.core.management.base import BaseCommand
from tenants.models import Client

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deactivate tenant'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema', help='Tentant schema name', required=True)

    def handle(self, *args, **options):

        tenant = Client.objects.filter(schema_name=options['schema']).first()

        if not tenant:
            self.stdout.write(f"Tenant schema does not exists {options['schema']}")
            return

        tenant.is_active = False
        tenant.save()
        
        self.stdout.write(f"Succesfully deactivated {options['schema']}")


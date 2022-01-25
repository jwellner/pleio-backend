from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from mixer.backend.django import mixer

from user.models import User


class Command(BaseCommand):
    help = 'Create random users with the same first name'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument('tenant')
        parser.add_argument('first_name')
        parser.add_argument('amount', type=int)

    def handle(self, *__, **options):
        with schema_context(options['tenant']):
            for x in range(options['amount']):
                user = mixer.blend(User)
                user.name = options['first_name'] + ' ' + user.name
                user.save()

        print("created users")

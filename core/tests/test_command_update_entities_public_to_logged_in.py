from unittest import mock

from mixer.backend.django import mixer

from core.management.commands.update_entities_public_to_logged_in import Command
from core.models import Entity
from core.lib import ACCESS_TYPE
from tenants.helpers import FastTenantTestCase


class UpdateEntitiesPublicToLoggedInTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.command = Command()
        self.command.stdout = mock.Mock()
        self.fake_tenant = 'no-tenant'

        mixer.cycle(10).blend(
            Entity,
            read_access=[ACCESS_TYPE.public, ACCESS_TYPE.user.format("123")],
            write_access=[ACCESS_TYPE.public, ACCESS_TYPE.user.format("123")]
        )
        mixer.cycle(5).blend(
            Entity,
            read_access=[ACCESS_TYPE.logged_in, ACCESS_TYPE.user.format("123")],
            write_access=[ACCESS_TYPE.user.format("123")]
        )
        mixer.cycle(2).blend(
            Entity,
            read_access=[ACCESS_TYPE.user.format("123")],
            write_access=[ACCESS_TYPE.logged_in, ACCESS_TYPE.user.format("123")]
        )

    def tearDown(self):
        Entity.objects.all().delete()
        super().tearDown()

    def test_update_read_access(self):
        self.command.handle()

        public_entities_count = Entity.objects.filter(read_access__overlap=list([ACCESS_TYPE.public])).count()
        logged_in_entities_count = Entity.objects.filter(read_access__overlap=list([ACCESS_TYPE.logged_in])).count()
        private_entities_count = Entity.objects.filter(read_access=[ACCESS_TYPE.user.format("123")]).count()

        self.assertEqual(public_entities_count, 0, 'Public read_access should be removed')
        self.assertEqual(logged_in_entities_count, 15, 'Public read_access should be made logged_in')
        self.assertEqual(private_entities_count, 2, 'Number of private entities should stay the same')

    def test_update_write_access(self):
        self.command.handle()

        public_entities_count = Entity.objects.filter(write_access__overlap=list([ACCESS_TYPE.public])).count()
        logged_in_entities_count = Entity.objects.filter(write_access__overlap=list([ACCESS_TYPE.logged_in])).count()
        private_entities_count = Entity.objects.filter(write_access=[ACCESS_TYPE.user.format("123")]).count()

        self.assertEqual(public_entities_count, 0, 'Public write_access should be removed')
        self.assertEqual(logged_in_entities_count, 12, 'Public write_access should be made logged_in')
        self.assertEqual(private_entities_count, 5, 'Number of private entities should stay the same')

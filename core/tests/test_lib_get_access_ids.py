from core.factories import GroupFactory
from core.lib import get_access_ids
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestLibGetAccessIds(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.override_config(IS_CLOSED=True)
        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner,
                                  name="Foo",
                                  is_closed=True)

    def tearDown(self):
        self.group.delete()
        self.owner.delete()
        super().tearDown()

    def test_get_group_access_ids(self):
        self.assertEqual(get_access_ids(self.group), [
            {"description": "Alleen eigenaar", "id": 0},
            {"description": "Groep: Foo", "id": 4},
        ])

    def test_get_open_group_access_ids(self):
        self.group.is_closed = False
        self.group.save()

        self.assertEqual(get_access_ids(self.group), [
            {"description": "Alleen eigenaar", "id": 0},
            {"description": "Groep: Foo", "id": 4},
            {"description": "Ingelogde gebruikers", "id": 1}
        ])

    def test_get_open_site_open_group_access_ids(self):
        self.override_config(IS_CLOSED=False)
        self.group.is_closed = False
        self.group.save()

        self.assertEqual(get_access_ids(self.group), [
            {"description": "Alleen eigenaar", "id": 0},
            {"description": "Groep: Foo", "id": 4},
            {"description": "Ingelogde gebruikers", "id": 1},
            {"description": "Iedereen (publiek zichtbaar)", "id": 2},
        ])

    def test_get_sub_group_closed_group_access_ids(self):
        subgroup = self.group.subgroups.create(name="Baz")

        self.assertEqual(get_access_ids(self.group), [
            {"description": "Alleen eigenaar", "id": 0},
            {"description": "Groep: Foo", "id": 4},
            {'description': 'Subgroep: Baz', 'id': subgroup.access_id}
        ])

    def test_get_open_site_open_group_access_with_sub_group_ids(self):
        subgroup = self.group.subgroups.create(name="Baz")
        self.override_config(IS_CLOSED=False)
        self.group.is_closed = False
        self.group.save()

        self.assertEqual(get_access_ids(self.group), [
            {"description": "Alleen eigenaar", "id": 0},
            {"description": "Groep: Foo", "id": 4},
            {'description': 'Subgroep: Baz', 'id': subgroup.access_id},
            {'description': 'Ingelogde gebruikers', 'id': 1},
            {'description': 'Iedereen (publiek zichtbaar)', 'id': 2},
        ])

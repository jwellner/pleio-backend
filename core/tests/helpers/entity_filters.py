from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class Template:
    class TestEntityFiltersTestCase(PleioTenantTestCase):
        include_activity_query = True
        include_entity_query = True

        _owner = None

        def get_owner(self):
            if not self._owner:
                self._owner = UserFactory()
            return self._owner

        def subtype_factory(self, **kwargs):
            raise NotImplementedError()

        def reference_factory(self, **kwargs):
            raise NotImplementedError()

        def get_subtype(self):
            raise NotImplementedError()

        def setUp(self):
            super().setUp()

            self.visitor = self.get_owner()

            self.article1 = self.subtype_factory(owner=self.get_owner())
            self.article2 = self.subtype_factory(owner=self.get_owner())

            self.reference1 = self.reference_factory(owner=self.get_owner())
            self.reference2 = self.reference_factory(owner=self.get_owner())

        def tearDown(self):
            self.article1.delete()
            self.article2.delete()
            self.reference1.delete()
            self.reference2.delete()
            if self._owner:
                self._owner.delete()
            super().tearDown()

        def test_entity_query(self):
            if not self.include_entity_query:
                return

            query = """
            query EntityQuery($subtype: String) {
                entities(subtype: $subtype) {
                    edges {
                        guid
                    }
                }
            }
            """

            self.graphql_client.force_login(self.visitor)
            result = self.graphql_client.post(query, {})

            guids = {e['guid'] for e in result['data']['entities']['edges']}
            self.assertEqual(guids, {self.article1.guid, self.article2.guid, self.reference1.guid, self.reference2.guid})

            self.graphql_client.force_login(self.visitor)
            result = self.graphql_client.post(query, {"subtype": self.get_subtype()})

            guids = {e['guid'] for e in result['data']['entities']['edges']}
            self.assertEqual(guids, {self.article1.guid, self.article2.guid})

        def test_activity_query(self):
            if not self.include_activity_query:
                return

            query = """
            query EntityQuery($subtypes: [String]) {
                activities(subtypes: $subtypes) {
                    edges {
                        guid
                    }
                }
            }
            """

            def activities(*guids):
                return {"activity:%s" % id for id in guids}

            self.graphql_client.force_login(self.visitor)
            result = self.graphql_client.post(query, {})

            guids = {e['guid'] for e in result['data']['activities']['edges']}
            self.assertEqual(guids, activities(self.article1.guid, self.article2.guid, self.reference1.guid, self.reference2.guid))

            self.graphql_client.force_login(self.visitor)
            result = self.graphql_client.post(query, {"subtypes": [self.get_subtype()]})

            guids = {e['guid'] for e in result['data']['activities']['edges']}
            self.assertEqual(guids, activities(self.article1.guid, self.article2.guid))

from mixer.backend.django import mixer

from core.models import Group, TagSynonym, Tag
from core.tests.helpers import ElasticsearchTestCase
from user.factories import UserFactory


class TestTagsSearchTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.group_f = mixer.blend(Group, name="Group F")
        self.group_f.tags = ['Fiets']
        self.group_f.save()

        self.authenticated_user = UserFactory(name='visitor')

        self.query = """
        query SearchGroups($q: String!) {
            search(q: $q) {
                edges {
                    ... on Group {
                        name
                    }
                }
            }
        }
        """
        self.variables = {
            'q': "Fiets"
        }

    def test_search_separate_tags(self):
        group_t = mixer.blend(Group, name="Group T")
        group_t.tags = ['Tweewieler']
        group_t.save()

        self.initialize_index()
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, self.variables)
        groups = [d['name'] for d in result['data']['search']['edges']]

        self.assertIn(self.group_f.name, groups)
        self.assertNotIn(group_t.name, groups)

    def test_search_combined_tags(self):
        TagSynonym.objects.create(label='tweewieler', tag=Tag.objects.get(label='fiets'))
        group_t = mixer.blend(Group, name="Group T")
        group_t.tags = ['Tweewieler']
        group_t.save()

        self.initialize_index()
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, self.variables)
        groups = [d['name'] for d in result['data']['search']['edges']]

        self.assertIn(self.group_f.name, groups)
        self.assertIn(group_t.name, groups)

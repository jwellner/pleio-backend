from ariadne import graphql_sync
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from core.models import Group, TagSynonym, Tag
from core.tests.helpers import ElasticsearchTestMixin
from user.models import User


class TestTagsSearchTestCase(FastTenantTestCase, ElasticsearchTestMixin):

    def setUp(self):
        super().setUp()

        self.group_f = mixer.blend(Group, name="Group F")
        self.group_f.tags = ['Fiets']
        self.group_f.save()

        self.request = HttpRequest()
        self.request.user = mixer.blend(User, name='visitor')

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

        success, result = graphql_sync(schema, {
            "query": self.query,
            "variables": self.variables,
        }, context_value={"request": self.request})

        self.assertNotIn('errors', result, msg=result)
        groups = [d['name'] for d in result['data']['search']['edges']]

        self.assertIn(self.group_f.name, groups)
        self.assertNotIn(group_t.name, groups)

    def test_search_combined_tags(self):
        TagSynonym.objects.create(label='tweewieler', tag=Tag.objects.get(label='fiets'))
        group_t = mixer.blend(Group, name="Group T")
        group_t.tags = ['Tweewieler']
        group_t.save()

        self.initialize_index()

        success, result = graphql_sync(schema, {
            "query": self.query,
            "variables": self.variables,
        }, context_value={"request": self.request})

        self.assertNotIn('errors', result, msg=result)
        groups = [d['name'] for d in result['data']['search']['edges']]

        self.assertIn(self.group_f.name, groups)
        self.assertIn(group_t.name, groups)

from core.constances import ACCESS_TYPE
from core.tests.helpers import ElasticsearchTestCase
from news.models import News
from user.factories import UserFactory
from blog.models import Blog
from mixer.backend.django import mixer

from wiki.models import Wiki


class SearchTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.common_tag1 = "Alles moet weg"
        self.common_tag2 = "Niets blijft staan"
        self.q = "Alles"

        self.user = UserFactory()

        permission = {
            'owner': self.user,
            'read_access': [ACCESS_TYPE.public],
            'write_access': [ACCESS_TYPE.user.format(self.user.guid)],
        }

        self.blog1 = mixer.blend(Blog, title=self.common_tag1, **permission)
        self.blog2 = mixer.blend(Blog, title=self.common_tag2, **permission)
        self.wiki1 = mixer.blend(Wiki, title=self.common_tag1, **permission)
        self.wiki2 = mixer.blend(Wiki, title=self.common_tag2, **permission)
        self.news1 = mixer.blend(News, title=self.common_tag1, **permission)
        self.news2 = mixer.blend(News, title=self.common_tag2, **permission)

    def test_invalid_subtype(self):
        query = """
            query Search(
                        $q: String!,
                        $subtypes: [String],
                        $subtype: String) {
                search( 
                        q: $q,
                        subtypes: $subtypes,
                        subtype: $subtype) {
                    edges {
                        guid
                    }
                }
            }
        """

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(query, {
                "q": "",
                "subtype": "test"
            })

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(query, {
                "q": "",
                "subtypes": ["test"]
            })

    def test_multiple_subtypes(self):
        query = """
            query Search(
                        $q: String!
                        $subtype: String
                        $subtypes: [String]) {
                search( 
                        q: $q,
                        subtype: $subtype
                        subtypes: $subtypes) {
                    edges {
                        guid
                    }
                    total
                    totals {
                        subtype
                        total
                    }
                }
            }
        """

        variables = {
            "q": self.q,
            "subtypes": ["blog", "wiki"],
            "subtype": "blog"
        }
        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(query, variables)

        data = result['data']['search']
        items = [i['guid'] for i in data['edges']]

        self.assertEqual(2, data['total'])
        self.assertEqual(1, len(items))
        self.assertIn(self.blog1.guid, items)
        self.assertNotIn(self.wiki1.guid, items)
        self.assertNotIn(self.news1.guid, items)

    def test_invalid_date(self):
        query = """
            query Search(
                        $q: String!,
                        $dateFrom: String,
                        $dateTo: String) {
                search( 
                        q: $q,
                        dateFrom: $dateFrom,
                        dateTo: $dateTo) {
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "q": "",
            "dateFrom": "2016-33-03T19:00:00",
            "dateTo": "2016-44-03T19:00:00"
        }

        self.initialize_index()

        with self.assertGraphQlError("invalid_date"):
            self.graphql_client.post(query, variables)

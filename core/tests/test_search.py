from mixer.backend.django import mixer

from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.models import Group
from core.tests.helpers import ElasticsearchTestCase
from file.models import FileFolder
from news.models import News
from user.factories import UserFactory
from wiki.models import Wiki

class SearchTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.common_tag1 = "Alles moet weg"
        self.common_tag2 = "Niets blijft staan"
        self.q = "Alles"
        
        self.group = mixer.blend(Group)
        self.user = UserFactory()

        self.query = """
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

        permission = {
            'owner': self.user,
            'read_access': [ACCESS_TYPE.public],
            'write_access': [ACCESS_TYPE.user.format(self.user.guid)],
        }

        self.pad = FileFolder.objects.create(
            type=FileFolder.Types.PAD,
            title="Test group pad",
            rich_description={"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"padtest"}]}]},
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            owner=self.user,
            group=self.group
        )

        self.blog1 = mixer.blend(Blog, title=self.common_tag1, **permission)
        self.blog2 = mixer.blend(Blog, title=self.common_tag2, **permission)
        self.wiki1 = mixer.blend(Wiki, title=self.common_tag1, **permission)
        self.wiki2 = mixer.blend(Wiki, title=self.common_tag2, **permission)
        self.news1 = mixer.blend(News, title=self.common_tag1, **permission)
        self.news2 = mixer.blend(News, title=self.common_tag2, **permission)

    def test_invalid_subtype(self):

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {
                "q": "",
                "subtype": "test"
            })

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {
                "q": "",
                "subtypes": ["test"]
            })

    def test_multiple_subtypes(self):

        variables = {
            "q": self.q,
            "subtypes": ["blog", "wiki", "pad"],
            "subtype": "blog"
        }
        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

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

    def test_pad_search(self):

        variables = {
            "q": "padtest",
            "subtype": "pad"
        }

        self.initialize_index()

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']['search']
        self.assertEqual(1, data['total'])

        self.assertEqual(self.pad.guid, data["edges"][0]["guid"])

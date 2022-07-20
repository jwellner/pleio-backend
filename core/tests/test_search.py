from core.tests.helpers import ElasticsearchTestCase
from user.factories import UserFactory
from blog.models import Blog
from mixer.backend.django import mixer

class SearchTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.blog1 = mixer.blend(Blog, title='Aa')
        self.blog2 = mixer.blend(Blog, title='Bb')
        self.blog3 = mixer.blend(Blog, title='Cc')

        self.user = UserFactory()

    def test_invalid_subtype(self):

        query = """
            query Search(
                        $q: String!,
                        $subtype: String) {
                search( 
                        q: $q,
                        subtype: $subtype) {
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "q": "",
            "subtype": "test"
        }

        with self.assertGraphQlError("invalid_subtype"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(query, variables)

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
import time
from blog.factories import BlogFactory
from core.tests.helpers import ElasticsearchTestCase, override_config
from external_content.factories import ExternalContentFactory, ExternalContentSourceFactory
from user.factories import UserFactory


class TestSearchExternalContentTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.external_author = UserFactory()
        self.author = UserFactory()

        with override_config(IS_CLOSED=False): # ACL is set on creation using the config
            self.source = ExternalContentSourceFactory(name="Source", plural_name="Source1's")
            self.source2 = ExternalContentSourceFactory(name="Source 2", plural_name="Source2's")

            self.article1 = ExternalContentFactory(title="Article 1",
                                                source=self.source,
                                                owner=self.external_author)
            self.article2 = ExternalContentFactory(title="Article 2",
                                                source=self.source,
                                                owner=self.external_author)
            self.article3 = ExternalContentFactory(title="Article 3",
                                                source=self.source,
                                                owner=self.external_author)
            self.article4 = ExternalContentFactory(title="Article 2.1",
                                                source=self.source2,
                                                owner=self.external_author)

        self.blog1 = BlogFactory(owner=self.author,
                                 title="Blog 1")
        self.blog2 = BlogFactory(owner=self.author,
                                 title="Blog 2")
        time.sleep(5)

    def tearDown(self):
        super().tearDown()

    @override_config(IS_CLOSED=False)
    def test_standard_search(self):
        query = """
        query ElasticSearchQuery($query: String
                      $subtype: String
                      $subtypes: [String]) {
            search(q: $query
                   subtype: $subtype
                   subtypes: $subtypes) {
                total
                totals {
                    subtype
                    total
                    title
                }
                edges {
                    guid
                }
            }
        }
        """

        result = self.graphql_client.post(query, {
            'query': '',
        })
        titles = sorted([t['title'] for t in result['data']['search']['totals']])
        self.assertEqual(titles, ["Blogs", "Source1's", "Source2's"])
        self.assertEqual(result['data']['search']['total'], 6)
        self.assertEqual(len(result['data']['search']['totals']), 3)
        self.assertEqual(len(result['data']['search']['edges']), 6)

        result = self.graphql_client.post(query, {
            'query': '',
            'subtype': self.source.guid
        })
        titles = sorted([t['title'] for t in result['data']['search']['totals']])
        self.assertEqual(titles, ["Blogs", "Source1's", "Source2's"])
        self.assertEqual(result['data']['search']['total'], 6)
        self.assertEqual(len(result['data']['search']['totals']), 3)
        self.assertEqual(len(result['data']['search']['edges']), 3)

        result = self.graphql_client.post(query, {
            'query': '',
            'subtypes': [self.source.guid]
        })
        titles = [t['title'] for t in result['data']['search']['totals']]
        self.assertEqual(titles, ["Source1's"])
        self.assertEqual(result['data']['search']['total'], 3)
        self.assertEqual(len(result['data']['search']['totals']), 1)
        self.assertEqual(len(result['data']['search']['edges']), 3)

    @override_config(IS_CLOSED=False)
    def test_entity_search(self):
        query = """
        query EntityQuery($orderBy: OrderBy
                          $orderDirection: OrderDirection
                          $subtype: String
                          $subtypes: [String]) {
            entities(orderBy: $orderBy
                     orderDirection: $orderDirection
                     subtype: $subtype
                     subtypes: $subtypes) {
                total
                edges {
                    guid
                    ... on Blog {
                        title
                    }
                    ... on ExternalContent {
                        title
                    }
                }
            }
        }
        """
        result = self.graphql_client.post(query, {})
        self.assertEqual(result['data']['entities']['total'], 6)
        self.assertEqual(len(result['data']['entities']['edges']), 6)

        result = self.graphql_client.post(query, {
            'subtype': self.source.guid,
            'orderBy': 'title',
            'orderDirection': 'asc',
        })
        titles = [edge['title'] for edge in result['data']['entities']['edges']]
        self.assertEqual(result['data']['entities']['total'], 3)
        self.assertEqual(len(result['data']['entities']['edges']), 3)
        self.assertEqual(titles, ["Article 1", "Article 2", "Article 3"])

        result = self.graphql_client.post(query, {
            'subtypes': [self.source.guid, self.source2.guid],
            'orderBy': 'title',
            'orderDirection': 'asc',
        })
        titles = [edge['title'] for edge in result['data']['entities']['edges']]
        self.assertEqual(result['data']['entities']['total'], 4)
        self.assertEqual(len(result['data']['entities']['edges']), 4)
        self.assertEqual(titles, ["Article 1", "Article 2", "Article 2.1", "Article 3"])

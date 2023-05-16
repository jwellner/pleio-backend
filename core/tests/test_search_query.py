import faker

from core.models import SearchQueryJournal
from core.tests.helpers import ElasticsearchTestCase
from user.factories import UserFactory


class TestQueryJournalTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.query = """
        query SearchQuery($query: String!) {
            search(q: $query) {
                total
            }
        }
        """
        self.variables = {
            "query": faker.Faker().name()
        }

    
    def tearDown(self):
        super().tearDown()

    def test_search_query_creates_a_journal_record(self):
        self.graphql_client.post(self.query, self.variables)

        self.assertEqual(SearchQueryJournal.objects.all().count(), 1)
        self.assertEqual(SearchQueryJournal.objects.first().query, self.variables['query'])

    def test_search_query_creates_one_record_per_session(self):
        self.graphql_client.force_login(self.authenticated_user)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)

        self.assertEqual(SearchQueryJournal.objects.all().count(), 1)

    def test_multiple_users_can_create_multiple_records_in_the_same_time(self):
        for n in range(0, 10):
            self.graphql_client.force_login(UserFactory())
            self.graphql_client.post(self.query, self.variables)

        self.assertEqual(SearchQueryJournal.objects.all().count(), 10)

    def test_empty_query_does_not_result_in_journal_records(self):
        for query in ['', ' ', '\n', '\t']:
            self.graphql_client.force_login(UserFactory())
            self.graphql_client.post(self.query, {"query": query})

        self.assertEqual(SearchQueryJournal.objects.all().count(), 0)

    def test_anonymous_query_results_in_journal_records(self):
        self.graphql_client.post(self.query, self.variables)

        record = SearchQueryJournal.objects.all().first()
        self.assertIsNotNone(record)
        self.assertIsNotNone(record.query)
        self.assertIsNotNone(record.session)

    def test_anonymous_query_creates_multiple_journal_records(self):
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)

        self.assertEqual(SearchQueryJournal.objects.all().count(), 1)

from django.utils import timezone

from core.factories import SearchQueryJournalFactory
from core.models import SearchQueryJournal
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, UserFactory


class TestQueryJournalTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestQueryJournalTestCase, self).setUp()

        self.FIRST = 'test'
        self.SECOND = 'test123'
        self.THIRD = 'test456'

        SearchQueryJournalFactory(query=self.FIRST)
        SearchQueryJournalFactory(query=self.FIRST)
        SearchQueryJournalFactory(query=self.FIRST)
        SearchQueryJournalFactory(query=self.FIRST)
        SearchQueryJournalFactory(query=self.FIRST)
        SearchQueryJournalFactory(query=self.THIRD)
        SearchQueryJournalFactory(query=self.SECOND)
        SearchQueryJournalFactory(query=self.SECOND)
        SearchQueryJournalFactory(query=self.SECOND)

        self.admin = AdminFactory()
        self.authenticated_user = UserFactory()

        self.query = """
        query SummariseQueryJournal(
                $start: DateTime,
                $end: DateTime
                $limit: Int
                $offset: Int) {
            searchJournal(
                    dateTimeFrom: $start
                    dateTimeTo: $end
                    limit: $limit
                    offset: $offset) {
                total
                edges {
                    count
                    query
                }
            }
        }
        """

    def test_aggregated_result_content(self):
        result = {n['query']: n['count'] for n in SearchQueryJournal.objects.last_month()}

        self.assertEqual(result[self.FIRST], 5)
        self.assertEqual(result[self.SECOND], 3)
        self.assertEqual(result[self.THIRD], 1)

    def test_aggregated_result_order(self):
        result = [n for n in SearchQueryJournal.objects.last_month()]

        self.assertEqual(result[0]['count'], 5)
        self.assertEqual(result[1]['count'], 3)
        self.assertEqual(result[2]['count'], 1)

    def test_query_limit(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'limit': 1
        })

        edges = result['data']['searchJournal']['edges']
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['query'], self.FIRST)

    def test_query_offset(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'offset': 1
        })

        edges = result['data']['searchJournal']['edges']
        self.assertEqual(2, result['data']['searchJournal']['total'])
        self.assertEqual(edges[0]['query'], self.SECOND)
        self.assertEqual(edges[1]['query'], self.THIRD)

    def test_query_offsetlimit(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'offset': 2,
            'limit': 1,
        })

        edges = result['data']['searchJournal']['edges']
        self.assertEqual(1, result['data']['searchJournal']['total'])
        self.assertEqual(edges[0]['query'], self.THIRD)

    def test_journal_factory_works(self):
        journal = SearchQueryJournalFactory()

        self.assertIsNotNone(journal.created_at)
        self.assertIsNotNone(journal.query)
        self.assertIsNone(journal.session)

    def test_anonymous_journal_factory(self):
        anonymousJournal = SearchQueryJournalFactory(session=None)

        self.assertIsNone(anonymousJournal.session)

    def test_query_as_user(self):
        with self.assertGraphQlError('user_not_site_admin'):
            self.graphql_client.force_login(self.authenticated_user)
            self.graphql_client.post(self.query, {})

    def test_query_as_anonymous_visitor(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.query, {})

    def test_query_without_arguments(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {})

        counts = [s['count'] for s in result['data']['searchJournal']['edges']]
        queries = [s['query'] for s in result['data']['searchJournal']['edges']]

        self.assertEqual(counts, [5, 3, 1])
        self.assertEqual(queries, [self.FIRST, self.SECOND, self.THIRD])

    def test_query_out_of_range(self):
        other_journal = SearchQueryJournalFactory(created_at=timezone.now() - timezone.timedelta(days=100))
        self.graphql_client.force_login(self.admin)

        # other_journal is to old.
        result = self.graphql_client.post(self.query, {})
        self.assertNotIn(other_journal.query, [s['query'] for s in result['data']['searchJournal']['edges']])

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'end': str(timezone.now() - timezone.timedelta(days=99))
        })

        # journals from setUp are to young
        self.assertNotIn(self.FIRST, [s['query'] for s in result['data']['searchJournal']['edges']])
        self.assertNotIn(self.SECOND, [s['query'] for s in result['data']['searchJournal']['edges']])
        self.assertNotIn(self.THIRD, [s['query'] for s in result['data']['searchJournal']['edges']])

        # other_journal it is in scope.
        self.assertIn(other_journal.query, [s['query'] for s in result['data']['searchJournal']['edges']])

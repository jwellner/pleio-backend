from blog.factories import BlogFactory
from core.elasticsearch import elasticsearch_status_report
from core.tests.helpers import PleioTenantTestCase, ElasticsearchTestCase
from user.factories import UserFactory


class TestCountNumberOfArticlesAtIndex(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        for n in range(0, 11):
            BlogFactory(owner=self.owner)

        ElasticsearchTestCase.initialize_index()

    def test_large_amount_of_articles(self):
        result = elasticsearch_status_report('blog')
        self.assertEqual(result, [
            {'actual': 11, 'alert': False, "expected": 11, 'index': 'blog'}
        ])

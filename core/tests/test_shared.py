from graphql import GraphQLError
from core.resolvers.shared import assert_valid_abstract
from tenants.helpers import FastTenantTestCase


class SharedTests(FastTenantTestCase):

    def test_clean_abstract(self):
        text = "x" * 320
        assert_valid_abstract(text)

    def test_clean_abstract_too_long(self):
        text = "x" * 321
        with self.assertRaises(GraphQLError):
            assert_valid_abstract(text)

    def test_clean_abstract_with_html(self):
        text = f"<p>{'x' * 320}</p>"
        assert_valid_abstract(text)

    def test_clean_abstract_too_long_with_html(self):
        text = f"<p>{'x' * 321}</p>"
        with self.assertRaises(GraphQLError):
            assert_valid_abstract(text)

    def test_clean_abstract_with_link(self):
        text = f"{'x' * 159}<a href=\"https://gibberish.nl\"></a>{'x' * 160}"
        assert_valid_abstract(text)

from unittest import mock

from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from event.factories import EventFactory


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    def get_subtype(self):
        return 'event'

    def subtype_factory(self, **kwargs):
        return EventFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)

    @mock.patch('activity.resolvers.query.complement_expected_range')
    def test_complement_extended_range_activities(self, complement_expected_range):
        # given.
        query = """query SomeQuery($subtypes: [String]) {
            activities(subtypes: $subtypes) {
                edges {
                    guid
                }
            }
        }
        """
        variables = {
            "subtypes": [self.get_subtype()]
        }

        # When.
        self.graphql_client.force_login(self.get_owner())
        self.graphql_client.post(query, variables)

        # Then.
        self.assertTrue(complement_expected_range.called)

    @mock.patch('activity.resolvers.query.complement_expected_range')
    def test_complement_extended_range_activities_any(self, complement_expected_range):
        # Given.
        query = """query SomeQuery {
            activities {
                edges {
                    guid
                }
            }
        }
        """
        variables = {}

        # When
        self.graphql_client.force_login(self.get_owner())
        self.graphql_client.post(query, variables)

        self.assertFalse(complement_expected_range.called)

    @mock.patch("core.resolvers.query_entities.complement_expected_range")
    def test_complement_extended_range_entities(self, complement_expected_range):
        # given.
        query = """query SomeQuery($subtypes: [String]) {
            entities(subtypes: $subtypes) {
                edges {
                    guid
                }
            }
        }
        """
        variables = {
            "subtypes": [self.get_subtype()]
        }

        # When.
        self.graphql_client.force_login(self.get_owner())
        self.graphql_client.post(query, variables)

        # Then.
        self.assertTrue(complement_expected_range.called)

    @mock.patch("core.resolvers.query_entities.complement_expected_range")
    def test_complement_extended_range_entities_any(self, complement_expected_range):
        # given.
        query = """query SomeQuery {
            entities {
                edges {
                    guid
                }
            }
        }
        """
        variables = {}

        # When.
        self.graphql_client.force_login(self.get_owner())
        self.graphql_client.post(query, variables)

        # Then.
        self.assertFalse(complement_expected_range.called)

    @mock.patch("event.resolvers.query.complement_expected_range")
    def test_complement_extended_range_events(self, complement_expected_range):
        # given.
        query = """query SomeQuery {
            entities {
                edges {
                    guid
                }
            }
        }
        """
        variables = {}

        # When.
        self.graphql_client.force_login(self.get_owner())
        self.graphql_client.post(query, variables)

        # Then.
        self.assertFalse(complement_expected_range.called)

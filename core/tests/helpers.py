import time
from contextlib import contextmanager

from datetime import datetime
from unittest import mock

from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils.crypto import get_random_string

from backend2.schema import schema
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from django.db.models import QuerySet
from collections import Counter


class PleioTenantTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.graphql_client = GraphQLClient()

    @contextmanager
    def assertGraphQlError(self, expected=None, msg=None):
        try:
            yield
            raise Exception("Unexpectedly didn't find any errors in graphql result")
        except GraphQlError as e:
            if not e.has_message(expected):
                self.fail(msg or f"Didn't find [{expected}] in {e.messages}")

    def assertDateEqual(self, left_date_string, right_date_string, *args, **kwargs):
        assert isinstance(left_date_string, str), "left_date_string should be a string. Is now %s." % type(
            left_date_string)
        assert isinstance(right_date_string, str), "right_date_string should be a string. Is now %s." % type(
            left_date_string)

        left = datetime.fromisoformat(left_date_string)
        right = datetime.fromisoformat(right_date_string)
        self.assertEqual(left, right, *args, **kwargs)


class GraphQlError(Exception):

    def __init__(self, data):
        self.data = data

    def has_message(self, expected=None):
        if expected:
            return expected in self.messages
        return True

    @property
    def messages(self):
        return [e['message'] for e in self.data['errors']]


class GraphQLClient():
    result = None
    request = None

    def __init__(self):
        self.reset()

    def reset(self):
        self.force_login(AnonymousUser())

    def force_login(self, user):
        self.request = HttpRequest()
        self.request.user = user
        self.request.COOKIES['sessionid'] = get_random_string(32)

    def post(self, query, variables):
        success, self.result = graphql_sync(schema, {"query": query,
                                                     "variables": variables},
                                            context_value={"request": self.request})

        if self.result.get('errors'):
            raise GraphQlError(self.result)

        return self.result


class ElasticsearchTestCase(PleioTenantTestCase):

    @staticmethod
    def initialize_index():
        with suppress_stdout():
            from core.lib import tenant_schema
            from core.tasks.elasticsearch_tasks import elasticsearch_recreate_indices, elasticsearch_index_data_for_tenant
            elasticsearch_recreate_indices()
            elasticsearch_index_data_for_tenant(tenant_schema(), None)
            time.sleep(.200)


class QuerySetWith:
    """ Class to help identify whether arguments are equal when a QuerySet is expected """

    def __init__(self, result):
        self.result = result

    def __eq__(self, value):
        if not isinstance(value, QuerySet):
            return False

        return Counter(list(value)) == Counter(self.result)


@contextmanager
def suppress_stdout():
    # pylint: disable=import-outside-toplevel
    from contextlib import redirect_stderr, redirect_stdout
    from os import devnull
    with mock.patch('warnings.warn'):
        with open(devnull, 'w') as fnull:
            with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
                yield (err, out)

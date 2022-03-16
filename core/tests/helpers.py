import unittest
from contextlib import contextmanager

import time
from django.db.models import QuerySet
from collections import Counter


class GraphqlTestMixin(unittest.TestCase):
    def assertGraphqlSuccess(self, result):
        self.assertTrue(result[0])

        self.assertIsNone(result[1].get("errors"))

    def assertGraphqlError(self, result, expectedError):
        self.assertTrue(result[0])

        self.assertIsNotNone(result[1].get("errors"))

        for error in result[1].get("errors"):
            self.assertEqual(error.get("message"), expectedError)


class ElasticsearchTestMixin():

    @staticmethod
    def initialize_index():
        from core.tasks import elasticsearch_recreate_indices, elasticsearch_repopulate_index_for_tenant
        from django_tenants.utils import parse_tenant_config_path

        with suppress_stdout():
            tenant_name = parse_tenant_config_path("")
            elasticsearch_recreate_indices()
            elasticsearch_repopulate_index_for_tenant(tenant_name, None)
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
    from contextlib import redirect_stderr, redirect_stdout
    from os import devnull

    with open(devnull, 'w') as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield (err, out)

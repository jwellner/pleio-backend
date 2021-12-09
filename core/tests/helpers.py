import unittest
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


class QuerySetWith:
    """ Class to help identify whether arguments are equal when a QuerySet is expected """
    def __init__(self, result):
        self.result = result

    def __eq__(self, value):
        if not isinstance(value, QuerySet):
            return False

        return Counter(list(value)) == Counter(self.result)

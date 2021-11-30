import unittest

class GraphqlTestMixin(unittest.TestCase):
    def assertGraphqlSuccess(self, result):
        self.assertTrue(result[0])

        self.assertIsNone(result[1].get("errors"))

    def assertGraphqlError(self, result, expectedError):
        self.assertTrue(result[0])

        self.assertIsNotNone(result[1].get("errors"))

        for error in result[1].get("errors"):
            self.assertEqual(error.get("message"), expectedError)

class GraphqlTestMixin:
    def assertGraphqlSuccess(self, result):
        self.assertTrue(result[0])

        self.assertIsNone(result[1].get("errors"))

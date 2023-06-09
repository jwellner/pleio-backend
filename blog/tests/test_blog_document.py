from blog.models import Blog
from core.tests.helpers import ElasticsearchTestCase
from user.models import User
from mixer.backend.django import mixer
from elasticsearch_dsl import Search, Q


class AddBlogTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = mixer.blend(User,
            name = "Jan de Vries"
        )
        self.data = mixer.blend(Blog,
            title = "test",
            owner = self.authenticatedUser
        )

        self.populate_index()

    def test_blog_document(self):
        s = Search(index='blog').query(
            Q('simple_query_string', query='Jan', fields=['owner.name'])
        ).filter(
            'term', tenant_name=self.tenant.schema_name
        )
        response = s.execute()

        for hit in response:
            self.assertEqual(hit.title, self.data.title)
            self.assertEqual(hit.owner.name, self.authenticatedUser.name)

        self.assertTrue(response)



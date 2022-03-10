
from django_tenants.test.cases import FastTenantTestCase
from blog.models import Blog
from user.models import User
from mixer.backend.django import mixer
from elasticsearch_dsl import Search, Q


class AddBlogTestCase(FastTenantTestCase):
    def setUp(self):
        self.authenticatedUser = mixer.blend(User,
            name = "Jan de Vries"
        )
        self.data = mixer.blend(Blog, 
            title = "test",
            owner = self.authenticatedUser
        )

    def test_blog_document(self):
        s = Search(index='_all').query(
            Q('simple_query_string', query='Jan', fields=['owner.name'])
            )
        response = s.execute()

        for hit in response:
            self.assertEqual(hit.title, self.data.title)
            self.assertEqual(hit.owner.name, self.authenticatedUser.name)

        self.assertTrue(response)

    

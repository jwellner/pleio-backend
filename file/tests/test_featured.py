from http import HTTPStatus

from mixer.backend.django import mixer

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class FeaturedTestCase(PleioTenantTestCase):

    def setUp(self):
        super(FeaturedTestCase, self).setUp()

        self.user = UserFactory()
        self.user2 = UserFactory()

        self.featured_file = self.file_factory(self.relative_path(__file__, ['assets', 'grass.jpg']))

        self.blog = mixer.blend(Blog, featured_image = self.featured_file)

    def test_embed_anonymous(self):
        response = self.client.get("/file/featured/{}".format(self.blog.id))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(hasattr(response, 'streaming_content'))
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')

    def test_embed_file(self):
        self.client.force_login(self.user)
        response = self.client.get("/file/featured/{}".format(self.blog.id))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(hasattr(response, 'streaming_content'))
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
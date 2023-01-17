import uuid

from django.urls import reverse

from blog.factories import BlogFactory
from core.constances import ACCESS_TYPE
from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestEntityViewTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.owner = UserFactory()
        self.visitor = UserFactory()
        self.blog = BlogFactory(owner=self.owner,
                                read_access=[ACCESS_TYPE.user.format(self.owner.guid)])
        self.group = GroupFactory(owner=self.owner)

    def tearDown(self):
        self.blog.delete()
        self.group.delete()
        self.visitor.delete()
        self.owner.delete()
        self.admin.delete()

        super().tearDown()

    def test_view_blog(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('entity_view', args=[self.blog.guid]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'react.html')

        self.client.force_login(self.visitor)
        response = self.client.get(reverse('entity_view', args=[self.blog.guid]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'react.html')

    def test_view_group(self):
        self.client.force_login(self.visitor)
        response = self.client.get(reverse("entity_view", args=[self.group.guid]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'react.html')

    def test_view_dumb_guess(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('entity_view', args=[uuid.uuid4()]))

        self.assertEqual(response.status_code, 404)

    def test_view_archived_blog(self):
        self.blog.is_archived = True
        self.blog.save()

        self.client.force_login(self.owner)
        response = self.client.get(reverse('entity_view', args=[self.blog.guid]))

        self.assertEqual(404, response.status_code)

    def test_view_draft_blog(self):
        self.blog.published = None
        self.blog.save()

        self.client.force_login(self.owner)
        response = self.client.get(reverse('entity_view', args=[self.blog.guid]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'react.html')

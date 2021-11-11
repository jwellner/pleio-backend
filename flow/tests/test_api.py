from http import HTTPStatus

from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from core import config
from core.models import Comment
from mixer.backend.django import mixer
from django.core.cache import cache
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from unittest import mock


class FlowApiTests(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.c = TenantClient(self.tenant)

        self.user1 = mixer.blend(User)

        cache.set("%s%s" % (connection.schema_name, 'FLOW_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'FLOW_SUBTYPES'), ['blog', 'discussion'])
        cache.set("%s%s" % (connection.schema_name, 'FLOW_APP_URL'), 'https://flow.test/')
        cache.set("%s%s" % (connection.schema_name, 'FLOW_TOKEN'), '12341234')
        cache.set("%s%s" % (connection.schema_name, 'FLOW_CASE_ID'), 1)
        cache.set("%s%s" % (connection.schema_name, 'FLOW_USER_GUID'), self.user1.guid)

    def tearDown(self):
        cache.clear()

    @mock.patch('requests.post')
    def test_add_comment(self, mocked_post):

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        self.data = {
            'container_guid': str(self.blog1.id),
            'description': 'test_description'
        }

        headers = {
            'Authorization': 'Bearer 12341234'
        }

        response = self.c.post("/flow/comments/add", headers=headers, data=self.data)

        comment = Comment.objects.all().first()
        self.assertEqual(comment.rich_description, 'test_description')
        self.assertEqual(str(comment.container.id), str(self.blog1.id))
        self.assertEqual(comment.owner, self.user1)


    @mock.patch('requests.post')
    def test_add_comment_no_description(self, mocked_post):

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        headers = {
            'Authorization': 'Bearer 12341234'
        }

        self.data = {
            'container_guid': str(self.blog1.id),
            'description': ''
        }

        response = self.c.post("/flow/comments/add", headers=headers, data=self.data)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


    @mock.patch('requests.post')
    def test_add_comment_no_container_guid(self, mocked_post):

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        headers = {
            'Authorization': 'Bearer 12341234'
        }

        self.data = {
            'container_guid': '',
            'description': 'test_description'
        }

        response = self.c.post("/flow/comments/add", headers=headers, data=self.data)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


    @mock.patch('requests.post')
    def test_add_comment_flow_disabled(self, mocked_post):

        cache.set("%s%s" % (connection.schema_name, 'FLOW_ENABLED'), False)

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        headers = {
            'Authorization': 'Bearer 12341234'
        }

        self.data = {
            'container_guid': str(self.blog1.id),
            'description': 'test_description'
        }

        response = self.c.post("/flow/comments/add", headers=headers, data=self.data)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


    @mock.patch('requests.post')
    def test_add_comment_wrong_token(self, mocked_post):

        cache.set("%s%s" % (connection.schema_name, 'FLOW_ENABLED'), False)

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        headers = {
            'Authorization': 'Bearer 12342'
        }

        self.data = {
            'container_guid': str(self.blog1.id),
            'description': 'test_description'
        }

        response = self.c.post("/flow/comments/add", headers=headers, data=self.data)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

# incorrect token

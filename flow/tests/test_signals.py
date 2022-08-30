import json
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.core.cache import cache
from core.models import Comment
from user.models import User
from blog.models import Blog
from core import config
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from unittest import mock
from flow.models import FlowId


class SignalsTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)

        cache.set("%s%s" % (connection.schema_name, 'FLOW_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'FLOW_SUBTYPES'), ['blog', 'discussion'])
        cache.set("%s%s" % (connection.schema_name, 'FLOW_APP_URL'), 'https://flow.test/')
        cache.set("%s%s" % (connection.schema_name, 'FLOW_TOKEN'), '12341234')
        cache.set("%s%s" % (connection.schema_name, 'FLOW_CASE_ID'), 1)
        cache.set("%s%s" % (connection.schema_name, 'FLOW_USER_GUID'), self.user1.guid)

        self.url_prefix = "https://tenant.fast-test.com"

    def tearDown(self):
        cache.clear()

    @mock.patch('requests.post')
    def test_object_and_comment_handler(self, mocked_post):

        mocked_post.return_value.json.return_value = {'id': 100}

        rich_description = json.dumps({
            'type': 'doc',
            'content': [
                {
                    'type': 'paragraph',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Dit is een '
                        },
                        {
                            'type': 'text',
                            'text': 'paragraph',
                            'marks': [{'type': 'bold'}],
                        }
                    ]
                }
            ]
        })

        rich_description_html = '<p>Dit is een <strong>paragraph</strong></p>'

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            abstract="abstract",
            rich_description=rich_description,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        url = 'https://flow.test/api/cases/'
        headers = {'Authorization': 'Token ' + config.FLOW_TOKEN, 'Accept': 'application/json'}

        description = f"{self.blog1.abstract}{rich_description_html}<p><a href='{self.url_prefix}{self.blog1.url}'>{self.blog1.url}</a></p>"
        json_data = {
            'casetype': '1',
            'name': 'Blog1',
            'description': description,
            'external_id': str(self.blog1.id),
            'external_author': self.blog1.owner.name,
            'tags': []
        }

        mocked_post.assert_called_with(url, headers=headers, json=json_data, timeout=30)

        self.comment1 = Comment.objects.create(
            rich_description="commenDescription1",
            owner=self.user1,
            container=self.blog1
        )


        url = 'https://flow.test/api/externalcomments/'

        case_id = FlowId.objects.get(object_id=self.blog1.id).flow_id
        json_data = {
            'case': str(case_id),
            'author': self.comment1.owner.name,
            'description': self.comment1.rich_description
        }

        mocked_post.assert_called_with(url, headers=headers, json=json_data, timeout=30)



    @mock.patch('requests.post')
    def test_object_and_comment_not_configured_handler(self, mocked_post):

        # blog not configured
        cache.set("%s%s" % (connection.schema_name, 'FLOW_SUBTYPES'), ['discussion'])

        mocked_post.return_value.json.return_value = {'id': 100}

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        url = 'https://flow.test/api/cases/'
        headers = {'Authorization': 'Token ' + config.FLOW_TOKEN, 'Accept': 'application/json'}

        description = f"{self.blog1.rich_description} <br /><br /><a href='{self.url_prefix}{self.blog1.url}'>{self.blog1.url}</a>"
        json_data = {
            'casetype': '1',
            'name': 'Blog1',
            'description': description,
            'external_id': str(self.blog1.id),
            'tags': []
        }

        mocked_post.assert_not_called

        cache.set("%s%s" % (connection.schema_name, 'FLOW_SUBTYPES'), ['blog', 'discussion'])

        self.comment1 = Comment.objects.create(
            rich_description='commenDescription1',
            owner=self.user1,
            container=self.blog1
        )

        mocked_post.assert_not_called


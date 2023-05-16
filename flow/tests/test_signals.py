import json
from django.db import connection
from django.core.cache import cache
from core.models import Comment
from tenants.helpers import FastTenantTestCase
from core.tests.helpers import override_config
from user.models import User
from blog.models import Blog
from core import config
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from unittest import mock
from flow.models import FlowId


class SignalsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)

        self.default_config = {
            'FLOW_ENABLED': True,
            'FLOW_SUBTYPES': ['blog', 'discussion'],
            'FLOW_APP_URL': 'https://flow.test/',
            'FLOW_TOKEN': '12341234',
            'FLOW_CASE_ID': 1,
            'FLOW_USER_GUID': self.user1.guid
        }

        self.url_prefix = "https://%s" % self.tenant.primary_domain

    def tearDown(self):
        cache.clear()
        super().tearDown()

    @mock.patch('requests.post')
    def test_object_and_comment_handler(self, mocked_post):

        with override_config(**self.default_config):

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
        new_config = {**self.default_config, 'FLOW_SUBTYPES': ['discussion']}
        with override_config(**new_config):
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

        new_config = {**self.default_config, 'FLOW_SUBTYPES': ['blog', 'discussion']}
        with override_config(**new_config):

            self.comment1 = Comment.objects.create(
                rich_description='commenDescription1',
                owner=self.user1,
                container=self.blog1
            )

            mocked_post.assert_not_called


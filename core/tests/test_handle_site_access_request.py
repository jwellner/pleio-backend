from django_tenants.test.cases import FastTenantTestCase
from django.contrib.auth.models import AnonymousUser
from user.models import User
from core.models import SiteAccessRequest
from core.constances import USER_ROLES
from mixer.backend.django import mixer
from backend2.schema import schema
from ariadne import graphql_sync
from django.http import HttpRequest
from unittest import mock
from django.test import override_settings


class HandleSiteAccessRequestTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.request1 = mixer.blend(SiteAccessRequest, email='test1@pleio.nl', claims={'email': 'test1@pleio.nl', 'name': 'Test 123', 'sub': 1})

        self.mutation = """
            mutation SiteAccessRequest($input: handleSiteAccessRequestInput!) {
                handleSiteAccessRequest(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        self.admin.delete()
        self.user.delete()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_handle_site_access_request.send_mail_multi.delay')
    def test_handle_access_request_by_admin(self, mocked_send_mail_multi):

        variables = {
            "input": {
                    "email": "test1@pleio.nl",
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertTrue(User.objects.filter(email=self.request1.email).exists())

        mocked_send_mail_multi.assert_called_once()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_handle_site_access_request.send_mail_multi.delay')
    def test_handle_access_request_deny_by_admin(self, mocked_send_mail_multi):

        variables = {
            "input": {
                    "email": "test1@pleio.nl",
                    "accept": False
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertFalse(User.objects.filter(email=self.request1.email).exists())
        
        mocked_send_mail_multi.assert_called_once()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_handle_site_access_request.send_mail_multi.delay')
    def test_handle_access_request_deny_silent_by_admin(self, mocked_send_mail_multi):

        variables = {
            "input": {
                    "email": "test1@pleio.nl",
                    "accept": False,
                    "silent": True
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertFalse(User.objects.filter(email=self.request1.email).exists())
        
        mocked_send_mail_multi.assert_not_called()

    def test_handle_access_request_by_user(self):

        variables = {
            "input": {
                    "email": "test1@pleio.nl",
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.user
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]


        self.assertEqual(errors[0]["message"], "user_not_site_admin")


    def test_handle_access_request_by_anonymous(self):

        variables = {
            "input": {
                    "email": "test1@pleio.nl", 
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


from django.conf import settings
from django.db import connection
from django.test import override_settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, GroupInvitation
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock

class AcceptMembershipRequestTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'pending')


    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user3.delete()
        self.user2.delete()
        self.user1.delete()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation MembershipRequestsList($input: acceptMembershipRequestInput!) {
                acceptMembershipRequest(input: $input) {
                    group {
                        guid
                        name
                        membershipRequests {
                            total
                            edges {
                                guid
                                username
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "userGuid": self.user2.guid, 
                "groupGuid": self.group1.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Request for access to the %s group has been approved" % self.group1.name)
        user_url = 'https://test.test' + self.user1.url

        self.assertEqual(data["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with(subject, 'email/accept_membership_request.html', {'user_name': self.user1.name, 'user_url': user_url, 
            'site_url': 'https://test.test', 'site_name': 'Pleio 2.0', 'primary_color': '#0e2f56', 'group_name': self.group1.name, 'link': link}, [self.user2.email])


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation MembershipRequestsList($input: acceptMembershipRequestInput!) {
                acceptMembershipRequest(input: $input) {
                    group {
                        guid
                        name
                        membershipRequests {
                            total
                            edges {
                                guid
                                username
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "userGuid": self.user2.guid, 
                "groupGuid": self.group1.guid
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Request for access to the %s group has been approved" % self.group1.name)
        user_url = 'https://test.test' + self.admin.url

        self.assertEqual(data["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with(subject, 'email/accept_membership_request.html', {'user_name': self.admin.name, 'user_url': user_url, 
            'site_url': 'https://test.test', 'site_name': 'Pleio 2.0', 'primary_color': '#0e2f56', 'group_name': self.group1.name, 'link': link}, [self.user2.email])

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_other_user(self, mocked_send_mail_multi):
        mutation = """
            mutation MembershipRequestsList($input: acceptMembershipRequestInput!) {
                acceptMembershipRequest(input: $input) {
                    group {
                        guid
                        name
                        membershipRequests {
                            total
                            edges {
                                guid
                                username
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "userGuid": self.user2.guid, 
                "groupGuid": self.group1.guid
                }
            }

        request = HttpRequest()
        request.user = self.user3
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_anonymous(self, mocked_send_mail_multi):
        mutation = """
            mutation MembershipRequestsList($input: acceptMembershipRequestInput!) {
                acceptMembershipRequest(input: $input) {
                    group {
                        guid
                        name
                        membershipRequests {
                            total
                            edges {
                                guid
                                username
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "userGuid": self.user2.guid, 
                "groupGuid": self.group1.guid
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
        assert not mocked_send_mail_multi.called

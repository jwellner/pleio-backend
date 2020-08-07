from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, GroupMembership
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class ChangeGroupRoleTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'member')
        self.group1.join(self.user4, 'admin')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user4.delete()
        self.user3.delete()
        self.user2.delete()
        self.user1.delete()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_owner_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
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
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Ownership of the %s group has been transferred" % self.group1.name)

        self.assertEqual(data["changeGroupRole"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_member_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    members {
                        total
                        edges {
                            role
                        }
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user4.guid,
                "role": "member"
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Ownership of the %s group has been transferred" % self.group1.name)

        self.assertEqual(data["changeGroupRole"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["changeGroupRole"]["group"]["members"]["total"], 2)
        self.assertEqual(data["changeGroupRole"]["group"]["members"]["edges"][1]["role"], "member")
        assert not mocked_send_mail_multi.called


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_removed_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    members {
                        total
                        edges {
                            role
                        }
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user4.guid,
                "role": "removed"
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Ownership of the %s group has been transferred" % self.group1.name)

        self.assertEqual(data["changeGroupRole"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["changeGroupRole"]["group"]["members"]["total"], 1)
        assert not mocked_send_mail_multi.called




    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_admin_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    members {
                        edges {
                            role
                        }
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "admin"
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))
        subject = ugettext_lazy("Ownership of the %s group has been transferred" % self.group1.name)

        self.assertEqual(data["changeGroupRole"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["changeGroupRole"]["group"]["members"]["edges"][0]["role"], "admin")
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_owner_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
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
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        subject = ugettext_lazy("Ownership of the %s group has been transferred" % self.group1.name)
        link = "https://test.test" + "/groups/view/{}/{}".format(self.group1.guid, slugify(self.group1.name))

        self.assertEqual(data["changeGroupRole"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_owner_by_other_user(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
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
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
                }
            }

        request = HttpRequest()
        request.user = self.user3
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_change_group_role.send_mail_multi')
    def test_change_group_role_to_owner_by_anonymous(self, mocked_send_mail_multi):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
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
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
        assert not mocked_send_mail_multi.called

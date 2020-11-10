from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class RevokeInviteToSiteTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])


    def tearDown(self):
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()


    def test_revoke_invite_to_site_by_admin(self):
        mutation = """
            mutation InviteItem($input: revokeInviteToSiteInput!) {
                revokeInviteToSite(input: $input) {
                    success
                }
            }
        """

        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl']
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["revokeInviteToSite"]["success"], True)


    def test_revoke_invite_to_site_by_user(self):
        mutation = """
            mutation InviteItem($input: revokeInviteToSiteInput!) {
                revokeInviteToSite(input: $input) {
                    success
                }
            }
        """

        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl']
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


    def test_revoke_invite_to_site_by_anonymous(self):
        mutation = """
            mutation InviteItem($input: revokeInviteToSiteInput!) {
                revokeInviteToSite(input: $input) {
                    success
                }
            }
        """

        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl']
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

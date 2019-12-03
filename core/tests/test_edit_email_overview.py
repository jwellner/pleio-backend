from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class EditEmailOverviewTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()


    def tearDown(self):
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()

    def test_edit_email_overview_by_owner(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input":  {
                "guid": self.user1.guid, 
                "overview": "monthly"
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editEmailOverview"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editEmailOverview"]["user"]["emailOverview"], "monthly")


    def test_edit_email_overview_by_admin(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input":  {
                "guid": self.user1.guid, 
                "overview": "monthly"
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editEmailOverview"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editEmailOverview"]["user"]["emailOverview"], "monthly")

    def test_edit_email_overview_by_logged_in_user(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input":  {
                "guid": self.user1.guid, 
                "overview": "monthly"
                }
            }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_edit_email_overview_by_anonymous(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input":  {
                "guid": self.user1.guid, 
                "overview": "monthly"
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

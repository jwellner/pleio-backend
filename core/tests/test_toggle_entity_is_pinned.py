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
from blog.models import Blog
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class ToggleEntityIsPinnedTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.group_admin = mixer.blend(User)
        self.group_user = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.group_admin)
        self.group.join(self.group_admin, 'admin')
        self.group.join(self.group_user, 'member')

        self.blog1 = mixer.blend(Blog, owner=self.user)
        self.blog2 = mixer.blend(Blog, owner=self.user, group=self.group)

    def tearDown(self):
        self.user.delete()
        self.admin.delete()
        self.group_admin.delete()
        self.group_user.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()

    def test_toggle_entity_is_pinned_by_anonymous(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_toggle_entity_is_pinned_by_user_no_group(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_toggle_is_pinned_by_admin_no_group(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_toggle_is_pinned_by_admin(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, True)

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, False)


    def test_toggle_is_pinned_by_group_admin(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        request = HttpRequest()
        request.user = self.group_admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, True)

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)
        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, False)

    def test_toggle_is_pinned_by_group_user(self):
        mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        request = HttpRequest()
        request.user = self.group_user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from core.models import Group, Comment
from user.models import User
from blog.models import Blog
from cms.models import Page
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from notifications.signals import notify


class SiteUsersTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name="specific_user_name_1")
        self.user3 = mixer.blend(User, is_delete_requested=True)
        self.admin1 = mixer.blend(User, is_admin=True)
        self.admin2 = mixer.blend(User, is_admin=True)
        self.anonymousUser = AnonymousUser()

        self.query = """
            query UsersQuery($offset: Int, $limit: Int, $q: String, $isAdmin: Boolean, $isDeleteRequested: Boolean) {

                siteUsers(offset: $offset, limit: $limit, q: $q, isAdmin: $isAdmin, isDeleteRequested: $isDeleteRequested) {
                    edges {
                        guid
                        name
                        url
                        icon
                        isAdmin
                        requestDelete
                    }
                    total
                }
            }
        """

    def tearDown(self):
            self.admin1.delete()
            self.admin2.delete()
            self.user1.delete()
            self.user2.delete()
            self.user3.delete()

    def test_site_users_get_all_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 5)
        self.assertEqual(len(data["siteUsers"]["edges"]), 5)

    def test_site_users_filter_admins_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "isAdmin": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 2)
        self.assertEqual(len(data["siteUsers"]["edges"]), 2)

    def test_site_users_filter_delete_requested_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "isDeleteRequested": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user3.guid)


    def test_site_users_filter_name_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "q": "c_user_nam"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)

    def test_site_users_by_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_site_users_by_user(self):

        request = HttpRequest()
        request.user = self.user1

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")

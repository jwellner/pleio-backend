from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from core.models import Group, Comment
from user.models import User
from blog.models import Blog
from cms.models import Page
from core.constances import ACCESS_TYPE, USER_ROLES
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from notifications.signals import notify
from django.utils import dateparse


class SiteUsersTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User, name="Tt")
        self.user2 = mixer.blend(User, name="Specific_user_name_1", email='specific@test.nl')
        self.user3 = mixer.blend(User, is_delete_requested=True, name="Zz")
        self.user4 = mixer.blend(User, is_active=False, name='Xx')
        self.user5 = mixer.blend(User)
        self.user5.delete()
        self.admin1 = mixer.blend(User, roles=[USER_ROLES.ADMIN], name='Yy')
        self.admin2 = mixer.blend(User, roles=[USER_ROLES.ADMIN], name='Uu')
        self.editor1 = mixer.blend(User, roles=[USER_ROLES.EDITOR], name='Vv')
        self.anonymousUser = AnonymousUser()

        self.user1.profile.last_online = dateparse.parse_datetime("2018-12-10T23:00:00.000Z")
        self.user1.profile.save()
        self.user3.profile.last_online = "2020-12-10T23:00:00.000Z"
        self.user3.profile.save()
        self.user4.profile.last_online = "2020-12-10T23:00:00.000Z"
        self.user4.profile.save()

        self.query = """
            query UsersQuery($offset: Int, $limit: Int, $q: String, $role: String, $isDeleteRequested: Boolean, $isBanned: Boolean, $lastOnlineBefore: String) {

                siteUsers(offset: $offset, limit: $limit, q: $q, role: $role, isDeleteRequested: $isDeleteRequested, isBanned: $isBanned, lastOnlineBefore: $lastOnlineBefore) {
                    edges {
                        guid
                        name
                        url
                        email
                        icon
                        roles
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
        self.user4.delete()

    def test_site_users_get_all_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 6)
        self.assertEqual(data["siteUsers"]["edges"][0]["name"], self.user2.name)
        self.assertEqual(len(data["siteUsers"]["edges"]), 6)

    def test_site_users_filter_admins_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "role": "admin"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 2)
        self.assertEqual(len(data["siteUsers"]["edges"]), 2)

    def test_site_users_filter_editors_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "role": "editor"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.editor1.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["roles"], self.editor1.roles)

    def test_site_users_filter_delete_requested_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "isDeleteRequested": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)


    def test_site_users_filter_email_guid_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "q": "specific@test.nl"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)


        variables = {
            "q": "cific@test.nl"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)


        variables = {
            "q": self.user2.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)




    def test_site_users_by_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_site_users_by_user(self):

        request = HttpRequest()
        request.user = self.user1

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


    def test_site_users_get_all_banned_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "isBanned": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)
        self.assertEqual(data["siteUsers"]["edges"][0]['guid'], self.user4.guid)


    def test_site_users_get_lastonline_before_by_admin(self):

        request = HttpRequest()
        request.user = self.admin1

        variables = {
            "lastOnlineBefore": "2019-12-10T23:00:00.000Z"
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["name"], self.user1.name)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)

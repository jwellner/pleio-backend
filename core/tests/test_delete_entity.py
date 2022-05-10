from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from django.test import override_settings
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from blog.models import Blog
from question.models import Question
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from user.models import User
from unittest import mock

class DeleteEntityTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group2 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'member')

        self.blog1 = mixer.blend(
            Blog,
            owner=self.user1,
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
        )
        self.question1 = mixer.blend(Question, owner=self.user1)
        self.groupBlog1 = mixer.blend(Blog, group=self.group1, owner=self.user1)
        self.groupQuestion1 = mixer.blend(Question, group=self.group1, owner=self.user1)


    def tearDown(self):
        self.blog1.delete()
        self.question1.delete()
        self.groupBlog1.delete()
        self.groupQuestion1.delete()

        self.group1.delete()
        self.group2.delete()

        self.user1.delete()
        self.user2.delete()
        self.admin.delete()

    def test_delete_entity_by_admin(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
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

        self.assertEqual(Blog.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)


    def test_delete_entity_by_owner(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
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
        request.user = self.user1

        self.assertEqual(Blog.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)


    def test_delete_entity_by_other_user(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
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
        request.user = self.user2

        self.assertEqual(Blog.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_delete_entity_by_anon(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
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

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_delete_group_by_admin(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        self.assertEqual(Blog.objects.all().count(), 2)
        self.assertEqual(Question.objects.all().count(), 2)
        self.assertEqual(Group.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)
        self.assertEqual(Question.objects.all().count(), 1)
        self.assertEqual(Group.objects.all().count(), 1)


    def test_delete_group_by_owner(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid
            }
        }

        request = HttpRequest()
        request.user = self.user1

        self.assertEqual(Blog.objects.all().count(), 2)
        self.assertEqual(Question.objects.all().count(), 2)
        self.assertEqual(Group.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)
        self.assertEqual(Question.objects.all().count(), 1)
        self.assertEqual(Group.objects.all().count(), 1)


    def test_delete_group_by_other_user(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid
            }
        }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_delete_group_by_anon(self):

        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_delete_archived(self):
        mutation = """
            mutation deleteEntity($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }
        self.blog1.is_archived = True
        self.blog1.save()

        request = HttpRequest()
        request.user = self.user1

        self.assertEqual(Blog.objects.all().count(), 2)

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)

from django.db import connection
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

class AddSubgroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.user1 = mixer.blend(User, name='a')
        self.user2 = mixer.blend(User, name='b')
        self.user3 = mixer.blend(User, name='c')
        self.user4 = mixer.blend(User, name='d')

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user2, 'member')
        self.group.join(self.user4, 'member')

    def tearDown(self):
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.admin.delete()

    def test_add_subgroup_by_group_owner(self):

        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid, self.user4.guid],
                "groupGuid": self.group.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addSubgroup"]["success"], True)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].name, 'testSubgroup')
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.filter(id=self.user2.guid)[0], self.user2)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.filter(id=self.user4.guid)[0], self.user4)

    def test_add_subgroup_by_admin(self):

        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid],
                "groupGuid": self.group.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addSubgroup"]["success"], True)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].name, 'testSubgroup')
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.all()[0], self.user2)


    def test_add_subgroup_by_group_member(self):

        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [],
                "groupGuid": self.group.guid
                }
            }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_add_subgroup_by_anonymous(self):

        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid],
                "groupGuid": self.group.guid
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_add_subgroup_with_non_group_member(self):

        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user3.guid],
                "groupGuid": self.group.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

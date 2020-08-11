from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Subgroup
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class DeleteSubgroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, is_admin=True) 
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User)        

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'member')
        self.group.join(self.user4, 'member')

        self.subgroup1 = Subgroup.objects.create(
            name='testSubgroup1',
            group=self.group
        )
        self.subgroup1.members.add(self.user2)
        self.subgroup1.members.add(self.user3)

        self.subgroup2 = Subgroup.objects.create(
            name='testSubgroup2',
            group=self.group
        )
        self.subgroup2.members.add(self.user2)
        self.subgroup2.members.add(self.user4)


    def tearDown(self):
        self.subgroup1.delete()
        self.subgroup2.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.admin.delete()


    def test_delete_subgroup_by_group_owner(self):

        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteSubgroup"]["success"], True)
        self.assertEqual(len(Group.objects.get(id=self.group.id).subgroups.all()), 1)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0], self.subgroup2)

    def test_delete_subgroup_by_admin(self):

        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteSubgroup"]["success"], True)
        self.assertEqual(len(Group.objects.get(id=self.group.id).subgroups.all()), 1)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0], self.subgroup2)

    def test_delete_subgroup_by_other_user(self):

        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
                }
            }

        request = HttpRequest()
        request.user = self.user3

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_delete_subgroup_by_anonymous(self):

        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

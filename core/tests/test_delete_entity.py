from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from blog.models import Blog
from question.models import Question
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from user.models import User


class DeleteEntityTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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
        super().tearDown()

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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

        self.assertEqual(Blog.objects.all().count(), 2)

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        self.assertEqual(Blog.objects.all().count(), 2)
        self.assertEqual(Question.objects.all().count(), 2)
        self.assertEqual(Group.objects.all().count(), 2)

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        self.assertEqual(Blog.objects.all().count(), 2)
        self.assertEqual(Question.objects.all().count(), 2)
        self.assertEqual(Group.objects.all().count(), 2)

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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
        self.assertEqual(Blog.objects.all().count(), 2)

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteEntity"]["success"], True)
        self.assertEqual(Blog.objects.all().count(), 1)

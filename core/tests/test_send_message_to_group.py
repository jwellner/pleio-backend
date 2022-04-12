from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Subgroup
from user.models import User
from mixer.backend.django import mixer
from unittest import mock
from datetime import timedelta
from django.utils import timezone


class SendMessageToGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user1.profile.last_online = timezone.now()
        self.user1.profile.save()
        self.user2 = mixer.blend(User)
        self.user2.profile.last_online = timezone.now()
        self.user2.profile.language = 'en'
        self.user2.profile.save()
        self.user3 = mixer.blend(User)
        self.user3.profile.last_online = timezone.now()
        self.user3.profile.save()
        self.user4 = mixer.blend(User)
        self.user4.profile.last_online = timezone.now()
        self.user4.profile.save()
        self.user5 = mixer.blend(User, is_active=False)
        self.user5.profile.last_online = timezone.now()
        self.user5.profile.save()
        self.user6 = mixer.blend(User)
        self.user6.profile.last_online = timezone.now() - timedelta(days=200)
        self.user6.profile.save()
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'member')
        self.group1.join(self.user3, 'member')
        self.group1.join(self.user5, 'member')
        self.group1.join(self.user6, 'member')
        self.subgroup = mixer.blend(Subgroup)
        self.subgroup.members.add(self.user2)
        self.subgroup.members.add(self.user3)
        self.subgroup.members.add(self.user4)

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()
        self.user5.delete()

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid, self.user5.guid, self.user6.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})
        data = result[1]["data"]

        self.assertEqual(data["sendMessageToGroup"]["group"]["guid"], self.group1.guid)

        expected = [self.user2.email,
                    self.user3.email]
        self.assertEqual([c.args[4] for c in mocked_send_mail_multi.call_args_list],
                         expected, msg="Expected to be send to two users with the initiator in the reply-to argument")

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_by_group_member(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_by_other_user(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user4

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_by_anonymous(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
        assert not mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_as_test_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid],
                "isTest": True
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 1)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_all_members_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_with_copy(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": True,
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_group_including_self_with_copy(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": True,
                "recipients": [self.user3.guid, self.user1.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_as_test_with_copy(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True,
                "sendCopyToSender": True,
                "isTest": True
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 1)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_all_members_with_copy(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True,
                "sendCopyToSender": True,
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 3)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_all_members_including_self_with_copy(self, mocked_send_mail_multi):
        self.group1.join(self.user1, 'member')
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True,
                "sendCopyToSender": True,
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertEqual(mocked_send_mail_multi.call_count, 3)

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi.delay')
    def test_send_message_to_subgroup_subset_members(self, mocked_send_mail_multi):
        self.group1.join(self.user1, 'member')
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
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
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "subGroup": self.subgroup.id,
            }
        }

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        mails = [a.args[4] for a in mocked_send_mail_multi.call_args_list]
        self.assertIn(self.user2.email, mails)
        self.assertIn(self.user3.email, mails)
        self.assertNotIn(self.user4.email, mails)
        self.assertEqual(mocked_send_mail_multi.call_count, 2, msg="Expect only members of the group AND the subgroup")

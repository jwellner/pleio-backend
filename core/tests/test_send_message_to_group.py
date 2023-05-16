from core.models import Group, Subgroup
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock
from datetime import timedelta
from django.utils import timezone


class SendMessageToGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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
        self.mutation = """
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

    def tearDown(self):
        super().tearDown()

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_by_group_owner(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid, self.user5.guid, self.user6.guid]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["sendMessageToGroup"]["group"]["guid"], self.group1.guid)

        mails = [a.kwargs['receiver'].email for a in mocked_mail.call_args_list]
        self.assertEqual(mails, [self.user2.email,
                                 self.user3.email],
                         msg="Expected to be send to two users with the initiator in the reply-to argument")

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid]
            }
        }

        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_by_group_member(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.mutation, variables)

        self.assertFalse(mocked_mail.called)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_by_other_user(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user4)
            self.graphql_client.post(self.mutation, variables)

        self.assertFalse(mocked_mail.called)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_by_anonymous(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)

        self.assertFalse(mocked_mail.called)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_as_test_by_group_owner(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid],
                "isTest": True
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_all_members_by_group_owner(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_with_copy(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": True,
                "recipients": [self.user3.guid]
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_group_including_self_with_copy(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": True,
                "recipients": [self.user3.guid, self.user1.guid]
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 2)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_as_test_with_copy(self, mocked_mail):
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
        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_all_members_with_copy(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True,
                "sendCopyToSender": True,
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 3)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_all_members_including_self_with_copy(self, mocked_mail):
        self.group1.join(self.user1, 'member')
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendToAllMembers": True,
                "sendCopyToSender": True,
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(mocked_mail.call_count, 3)

    @mock.patch('core.resolvers.mutation_send_message_to_group.schedule_group_message_mail')
    def test_send_message_to_subgroup_subset_members(self, mocked_mail):
        self.group1.join(self.user1, 'member')
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "subGroup": self.subgroup.id,
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        mails = [a.kwargs['receiver'].email for a in mocked_mail.call_args_list]
        self.assertIn(self.user2.email, mails)
        self.assertIn(self.user3.email, mails)
        self.assertNotIn(self.user4.email, mails)
        self.assertEqual(mocked_mail.call_count, 2, msg="Expect only members of the group AND the subgroup")

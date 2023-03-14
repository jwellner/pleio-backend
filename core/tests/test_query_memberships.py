from core.models import Group, GroupProfileFieldSetting, ProfileField, UserProfile, UserProfileField
from core.tests.helpers import ElasticsearchTestCase
from user.factories import UserFactory
from user.models import User

from mixer.backend.django import mixer


class FilterUsersTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory(name="Owner", email='owner@example.com')
        self.group = mixer.blend(Group, owner=self.owner, introduction='introductionMessage')
        self.group.join(self.owner, 'owner')

        self.admin = UserFactory(name="Admin", email='admin@example.com')
        self.group.join(self.admin, 'admin')

        self.profile_field, created = ProfileField.objects.get_or_create(key='multi_key', is_filter=True,
                                                                         name='multi_name',
                                                                         field_type='multi_select_field',
                                                                         field_options=['select_value_1',
                                                                                        'select_value_2',
                                                                                        'select_value_3'])
        self.group_profile_field_setting, created = GroupProfileFieldSetting.objects.get_or_create(
            profile_field=self.profile_field,
            group=self.group,
            show_field=True
        )

        self.member1 = mixer.blend(User, name="Member 1", email='member1@example.com')
        self.group.join(self.member1, 'member')
        self.profile1, created = UserProfile.objects.get_or_create(user=self.member1)
        self.user_profile_field1, created = UserProfileField.objects.get_or_create(
            user_profile=self.profile1,
            profile_field=self.profile_field,
            value='select_value_1')

        self.member2 = mixer.blend(User, name="Member 2", email='member2@example.com')
        self.group.join(self.member2, 'member')
        self.profile2, created = UserProfile.objects.get_or_create(user=self.member2)
        self.user_profile_field2, created = UserProfileField.objects.get_or_create(
            user_profile=self.profile2,
            profile_field=self.profile_field,
            value='select_value_2')

        self.member3 = mixer.blend(User, name="Member 3", email='member3@example.com')
        self.group.join(self.member3, 'member')

        self.pending_member = mixer.blend(User, name="Pending Member", email='pending@example.com')
        self.group.join(self.pending_member, 'pending')

        self.not_a_member = mixer.blend(User, name="Outsider", email='outsider@example.com')

        self.query = """
            query MembersQuery ($groupGuid: String!
                                $query: String
                                $filters: [FilterInput]
                                $offset: Int
                                $limit: Int) {
                members(groupGuid: $groupGuid
                        q: $query
                        filters: $filters
                        offset: $offset
                        limit: $limit) {
                    total
                    edges {
                        role
                        email
                        memberSince
                        user {
                            guid
                        }
                    }
                }
            }
        """

    def tearDown(self):
        self.owner.delete()
        self.group.delete()
        self.admin.delete()
        self.profile_field.delete()
        self.group_profile_field_setting.delete()
        self.member1.delete()
        self.profile1.delete()
        self.user_profile_field1.delete()
        self.member2.delete()
        self.profile2.delete()
        self.user_profile_field2.delete()
        self.member3.delete()
        self.pending_member.delete()
        self.not_a_member.delete()
        super().tearDown()

    def graphql_sync_data(self, query, variables, visitor):
        self.graphql_client.force_login(visitor)
        result = self.graphql_client.post(query, variables)
        return result.get('data')

    def test_query_should_fail_for_anonymous_visitors(self):
        variables = {
            "groupGuid": str(self.group.guid)
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.query, variables)

    def test_query_should_fail_for_non_members(self):
        variables = {
            "groupGuid": str(self.group.guid)
        }

        with self.assertGraphQlError("user_not_member_of_group"):
            self.graphql_client.force_login(self.not_a_member)
            self.graphql_client.post(self.query, variables)

    def test_query_should_give_enhanced_response(self):
        variables = {
            "groupGuid": str(self.group.guid)
        }

        data = self.graphql_sync_data(self.query, variables, self.owner)
        members = data['members']['edges']

        self.assertEqual(data['members']['total'], 5)
        self.assertEqual(len(members), 5)
        owner = self.owner.memberships.get(group=self.group)
        self.assertEqual(members[0]['role'], "owner")
        self.assertEqual(members[0]['email'], owner.user.email)
        self.assertEqual(members[0]['memberSince'], owner.created_at.isoformat())
        admin = self.admin.memberships.get(group=self.group)
        self.assertEqual(members[1]['role'], "admin")
        self.assertEqual(members[1]['email'], admin.user.email)
        self.assertEqual(members[1]['memberSince'], admin.created_at.isoformat())
        member1 = self.member1.memberships.get(group=self.group)
        self.assertEqual(members[2]['role'], "member")
        self.assertEqual(members[2]['email'], member1.user.email)
        self.assertEqual(members[2]['memberSince'], member1.created_at.isoformat())
        member2 = self.member2.memberships.get(group=self.group)
        self.assertEqual(members[3]['role'], "member")
        self.assertEqual(members[3]['email'], member2.user.email)
        self.assertEqual(members[3]['memberSince'], member2.created_at.isoformat())
        member3 = self.member3.memberships.get(group=self.group)
        self.assertEqual(members[4]['role'], "member")
        self.assertEqual(members[4]['email'], member3.user.email)
        self.assertEqual(members[4]['memberSince'], member3.created_at.isoformat())

    def test_full_text_query_should_ignore_non_members(self):
        self.not_a_member.name = self.not_a_member.guid
        self.not_a_member.save()

        variables = {
            "groupGuid": str(self.group.guid),
            "query": self.not_a_member.name
        }
        data = self.graphql_sync_data(self.query, variables, self.owner)

        self.assertEqual(data['members']['total'], 0,
                         msg="Resultaat gevonden, not-a-member lijkt tussen de members te staan.")

    def test_full_text_query_should_include_members(self):
        self.member1.name = self.member1.guid
        self.member1.save()

        variables = {
            "groupGuid": str(self.group.guid),
            "query": self.member1.name
        }

        data = self.graphql_sync_data(self.query, variables, self.owner)

        self.assertEqual(data['members']['total'], 1, msg="We verwachten 1 resultaat bij zoeken naar leden met een specifieke naam.")
        self.assertEqual(data['members']['edges'][0]['user']['guid'], str(self.member1.id))

    def test_query_should_find_profile_field_match(self):
        variables = {
            "groupGuid": str(self.group.guid),
            "filters": [{
                "name": self.profile_field.key,
                "values": ["select_value_1"]
            }]
        }
        data = self.graphql_sync_data(self.query, variables, self.owner)

        self.assertEqual(data['members']['total'], 1, msg="Expected one result")
        self.assertEqual(data['members']['edges'][0]['user']['guid'], self.member1.guid)

    def test_query_should_respect_offset(self):
        variables = {
            "groupGuid": str(self.group.guid),
            "offset": 2
        }
        data = self.graphql_sync_data(self.query, variables, self.owner)

        self.assertEqual(data['members']['edges'][0]['role'], 'member')
        self.assertEqual(len(data['members']['edges']), 3)

    def test_query_should_respect_limit(self):
        variables = {
            "groupGuid": str(self.group.guid),
            "limit": 2
        }
        data = self.graphql_sync_data(self.query, variables, self.owner)

        self.assertEqual(data['members']['edges'][0]['role'], 'owner')
        self.assertEqual(data['members']['edges'][1]['role'], 'admin')
        self.assertEqual(len(data['members']['edges']), 2)

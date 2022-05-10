from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from backend2.schema import schema
from core.models import Group, GroupProfileFieldSetting, ProfileField, UserProfile, UserProfileField

from core.tests.helpers import ElasticsearchTestMixin
from user.models import User

from ariadne import graphql_sync
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer


class FilterUsersTestCase(FastTenantTestCase, ElasticsearchTestMixin):

    def setUp(self):
        self.anonymous_user = AnonymousUser()
        self.owner = mixer.blend(User, name="Owner")
        self.group = mixer.blend(Group, owner=self.owner, introduction='introductionMessage')
        self.group.join(self.owner, 'owner')

        self.admin = mixer.blend(User, name="Admin")
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

        self.member1 = mixer.blend(User, name="Member 1")
        self.group.join(self.member1, 'member')
        self.profile1, created = UserProfile.objects.get_or_create(user=self.member1)
        self.user_profile_field1, created = UserProfileField.objects.get_or_create(
            user_profile=self.profile1,
            profile_field=self.profile_field,
            value='select_value_1')

        self.member2 = mixer.blend(User, name="Member 2")
        self.group.join(self.member2, 'member')
        self.profile2, created = UserProfile.objects.get_or_create(user=self.member2)
        self.user_profile_field2, created = UserProfileField.objects.get_or_create(
            user_profile=self.profile2,
            profile_field=self.profile_field,
            value='select_value_2')

        self.member3 = mixer.blend(User, name="Member 3")
        self.group.join(self.member3, 'member')

        self.pending_member = mixer.blend(User, name="Pending Member")
        self.group.join(self.pending_member, 'pending')

        self.not_a_member = mixer.blend(User, name="Outsider")

    def teardown(self):
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

    def graphql_sync_data(self, query, variables, visitor):
        success, response = self.graphql_sync(query, variables, visitor)

        errors = response.get('errors')
        self.assertIsNone(errors, msg=errors)
        return response.get('data')

    def graphql_sync(self, query, variables, visitor):
        request = HttpRequest()
        request.user = visitor
        return graphql_sync(schema, {"query": query,
                                     "variables": variables},
                            context_value={"request": request})

    def test_query_should_give_enhanced_response(self):
        query = """
            query MembersQuery ($groupGuid: String!) {
                members(groupGuid: $groupGuid) {
                    total
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """

        variables = {
            "groupGuid": str(self.group.guid)
        }

        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['total'], 5)
        self.assertEqual(len(data['members']['edges']), 5)
        self.assertEqual(data['members']['edges'][0]['role'], 'owner',
                         msg="Onverwachte volgorde van het resultaat: begint niet met de eigenaar.")
        self.assertEqual(data['members']['edges'][1]['role'], 'admin',
                         msg="Onverwachte volgorde van het resultaat: 2e is niet de admin.")
        self.assertEqual(data['members']['edges'][2]['role'], 'member',
                         msg="Onverwachte volgorde van het resultaat: 3e is niet member.")

    def test_full_text_query_should_ignore_non_members(self):
        query = """
            query MembersQuery ($groupGuid: String!, $query: String) {
                members(groupGuid: $groupGuid, q: $query) {
                    total
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """

        self.not_a_member.name = self.not_a_member.guid
        self.not_a_member.save()

        self.initialize_index()

        variables = {
            "groupGuid": str(self.group.guid),
            "query": self.not_a_member.name
        }
        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['total'], 0,
                         msg="Resultaat gevonden, not-a-member lijkt tussen de members te staan.")

    def test_full_text_query_should_include_members(self):
        query = """
            query MembersQuery ($groupGuid: String!, $query: String) {
                members(groupGuid: $groupGuid, q: $query) {
                    total
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """

        self.member1.name = self.member1.guid
        self.member1.save()

        self.initialize_index()

        variables = {
            "groupGuid": str(self.group.guid),
            "query": self.member1.name
        }

        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['total'], 1, msg="We verwachten 1 resultaat bij zoeken naar leden met een specifieke naam.")
        self.assertEqual(data['members']['edges'][0]['user']['guid'], str(self.member1.id))

    def test_query_should_find_profile_field_match(self):
        query = """
            query MembersQuery ($groupGuid: String!, $filters: [FilterInput]) {
                members(groupGuid: $groupGuid, filters: $filters) {
                    total
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """

        self.initialize_index()

        variables = {
            "groupGuid": str(self.group.guid),
            "filters": [{
                "name": self.profile_field.key,
                "values": ["select_value_1"]
            }]
        }
        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['total'], 1, msg="Expected one result")
        self.assertEqual(data['members']['edges'][0]['user']['guid'], self.member1.guid)

    def test_query_should_respect_offset(self):
        query = """
            query MembersQuery ($groupGuid: String!, $offset: Int) {
                members(groupGuid: $groupGuid, offset: $offset) {
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """
        self.initialize_index()

        variables = {
            "groupGuid": str(self.group.guid),
            "offset": 2
        }
        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['edges'][0]['role'], 'member')
        self.assertEqual(len(data['members']['edges']), 3)

    def test_query_should_respect_limit(self):
        query = """
            query MembersQuery ($groupGuid: String!, $limit: Int) {
                members(groupGuid: $groupGuid, limit: $limit) {
                    edges {
                        role
                        user {
                            guid
                        }
                    }
                }
            }
        """
        self.initialize_index()

        variables = {
            "groupGuid": str(self.group.guid),
            "limit": 2
        }
        data = self.graphql_sync_data(query, variables, self.owner)

        self.assertEqual(data['members']['edges'][0]['role'], 'owner')
        self.assertEqual(data['members']['edges'][1]['role'], 'admin')
        self.assertEqual(len(data['members']['edges']), 2)

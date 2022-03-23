from mixer.backend.django import mixer
from django.contrib.auth.models import AnonymousUser
from django_tenants.test.cases import FastTenantTestCase

from core.models import Group, ProfileField, GroupProfileFieldSetting, UserProfile, UserProfileField
from core.resolvers.filters import get_filter_options
from user.models import User

from core.tests.helpers import ElasticsearchTestMixin


class FiltersResolverTestCase(FastTenantTestCase, ElasticsearchTestMixin):

    def setUp(self):
        self.cleanup = []
        self.anonymousUser = AnonymousUser()
        self.owner = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.owner)
        self.group.join(self.owner, 'owner')
        self.member = mixer.blend(User)
        self.group.join(self.member, 'member')

        self.other_group = mixer.blend(Group, owner=self.owner)
        self.other_group.join(self.owner)
        self.other_member = mixer.blend(User)
        self.other_group.join(self.other_member, 'member')

        self.profile_options = ['select_value_1',
                                'select_value_2',
                                'select_value_3']

        self.profile_field = mixer.blend(ProfileField, key='multi_key', is_filter=True,
                                         name='multi_name',
                                         field_type='multi_select_field',
                                         field_options=self.profile_options)
        mixer.blend(GroupProfileFieldSetting,
                    profile_field=self.profile_field,
                    group=self.group,
                    show_field=True)
        mixer.blend(GroupProfileFieldSetting,
                    profile_field=self.profile_field,
                    group=self.other_group,
                    show_field=True)

        profile, created = UserProfile.objects.get_or_create(user=self.member)
        mixer.blend(UserProfileField,
                    profile_field=self.profile_field,
                    user_profile=profile,
                    read_access=['public'],
                    value=self.profile_options[0])
        other_profile, created = UserProfile.objects.get_or_create(user=self.other_member)
        mixer.blend(UserProfileField,
                    profile_field=self.profile_field,
                    user_profile=other_profile,
                    read_access=['public'],
                    value=self.profile_options[1])

    def test_filter_options_should_give_used_options(self):
        self.initialize_index()
        options = get_filter_options(self.profile_field.key, self.owner)

        self.assertEqual(len(options), 2, msg="We verwachten 2 waarden.")
        self.assertTrue(self.profile_options[0] in options, msg="Verwacht de waarde `%s` in het resultaat." % self.profile_options[0])
        self.assertTrue(self.profile_options[1] in options, msg="Verwacht de waarde `%s` in het resultaat." % self.profile_options[1])

    def test_filter_options_should_take_group_membership_into_account(self):
        self.initialize_index()
        options = get_filter_options(self.profile_field.key, self.owner, self.group)

        self.assertEqual(len(options), 1, msg="We verwachten 1 waarde.")
        self.assertTrue(self.profile_options[0] in options, msg="Verwacht de waarde `%s` in het resultaat." % self.profile_options[0])

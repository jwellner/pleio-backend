import uuid
from http import HTTPStatus

from django.test import override_settings
from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase, override_config
from user.models import User
from core.models import ProfileField, UserProfileField
from mixer.backend.django import mixer


class OnboardingTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        # Prepare fields
        self.profile_field1 = ProfileField.objects.create(
            key="profile_field1",
            name="profile_field1_name",
        )
        self.profile_field_multiselect = ProfileField.objects.create(
            key="profile_field_multiselect",
            name="profile_field_multi_select",
            field_type='multi_select_field',
            field_options=['Foo', 'Bar', 'Baz'],
        )
        self.profile_field_datefield = ProfileField.objects.create(
            key="profile_field_datefield",
            name="profile_field_datefield",
            field_type='date_field',
        )
        ProfileField.objects.update(is_mandatory=True,
                                    is_in_onboarding=True)

        # prepare existing user
        self.existing_user = mixer.blend(User, is_active=True)

    def tearDown(self):
        super().tearDown()

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect(self):
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user'
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_with_only_intro(self):
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user'
        })

        self.profile_field1.delete()

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_passed_if_no_intro_or_profile_fields(self):
        ProfileField.objects.all().delete()
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user'
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'base_closed.html')

    def test_onboarding_passes_when_logged_in_without_profile_field(self):
        ProfileField.objects.all().delete()
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user'
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO=None,
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            self.client.force_login(self.existing_user)
            response = self.client.get('/onboarding')

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, '/')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_create_user(self):
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user',
            'picture': None,
            'is_government': False,
            'has_2fa_enabled': True,
            'sub': '1234',
            'is_superadmin': False
        })

        expected_date = timezone.now()

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.post("/onboarding", data={
                self.profile_field1.guid: "Field1 value",
                self.profile_field_multiselect.guid: ["Foo", "Bar"],
                self.profile_field_datefield.guid: expected_date.strftime("%d-%m-%Y"),
            })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/")

        new_user = User.objects.filter(external_id="1234").first()
        self.assertEqual(new_user.email, 'test@pleio.nl')
        self.assertEqual(new_user.has_2fa_enabled, True)

        current_profile = {field.profile_field.guid: field.value for field in UserProfileField.objects.filter(user_profile=new_user.profile)}
        self.assertDictEqual(current_profile, {
            self.profile_field1.guid: "Field1 value",
            self.profile_field_multiselect.guid: "Foo,Bar",
            self.profile_field_datefield.guid: expected_date.strftime("%Y-%m-%d"),
        })

    def test_non_mandatory_onboarding(self):
        ProfileField.objects.update(is_mandatory=False)
        self.update_session(onboarding_claims={
            'email': 'test@pleio.nl',
            'name': 'test user',
            'sub': '1234',
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.post("/onboarding")

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/")

        new_user = User.objects.filter(external_id="1234").first()
        self.assertTrue(new_user)
        self.assertEqual(new_user.email, "test@pleio.nl")

        current_profile = {field.profile_field.guid: field.value for field in UserProfileField.objects.filter(user_profile=new_user.profile)}
        self.assertDictEqual(current_profile, {
            self.profile_field1.guid: "",
            self.profile_field_multiselect.guid: "",
            self.profile_field_datefield.guid: "",
        })

    def test_onboarding_logged_in_user(self):
        expected_prepopulated_value = str(uuid.uuid4())
        prepopulated_date = '2014-10-10'
        expected_date = '10-10-2014'
        UserProfileField.objects.create(user_profile=self.existing_user.profile,
                                        profile_field=self.profile_field1,
                                        value=expected_prepopulated_value)
        UserProfileField.objects.create(user_profile=self.existing_user.profile,
                                        profile_field=self.profile_field_multiselect,
                                        value='Foo')
        UserProfileField.objects.create(user_profile=self.existing_user.profile,
                                        profile_field=self.profile_field_datefield,
                                        value=prepopulated_date)
        self.update_session(onboarding_claims={
            'email': self.existing_user.email,
            'name': self.existing_user.name,
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            self.client.force_login(self.existing_user)
            response = self.client.get("/onboarding")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "onboarding.html")
        self.assertIn(expected_prepopulated_value, response.content.decode())
        self.assertIn(expected_date, response.content.decode())

    def test_onboarding_logged_in_user_with_invalid_date_value(self):
        expected_prepopulated_value = str(uuid.uuid4())
        UserProfileField.objects.create(user_profile=self.existing_user.profile,
                                        profile_field=self.profile_field_datefield,
                                        value=expected_prepopulated_value)
        self.update_session(onboarding_claims={
            'email': self.existing_user.email,
            'name': self.existing_user.name,
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            self.client.force_login(self.existing_user)
            response = self.client.get("/onboarding")

        self.assertNotIn(expected_prepopulated_value, response.content.decode())

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_no_claim(self):
        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'base_closed.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect_existing_off(self):
        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            self.client.force_login(self.existing_user)
            response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect_existing_on(self):
        self.client.force_login(self.existing_user)

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=True,
        ):
            response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_off(self):
        self.client.force_login(self.existing_user)

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=False,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    def test_onboarding_default_acl(self):
        ProfileField.objects.update(is_mandatory=False)
        self.update_session(onboarding_claims={
            'email': 'test_acl@pleio.nl',
            'name': 'test user',
            'sub': '4321',
        })

        with override_config(
            PROFILE_SECTIONS=[{"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}],
            IS_CLOSED=True,
            ONBOARDING_ENABLED=True,
            ONBOARDING_INTRO="There is an intro",
            ONBOARDING_FORCE_EXISTING_USERS=False,
        ):
            response = self.client.post("/onboarding")

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/")

        new_user = User.objects.filter(external_id="4321").first()
        self.assertTrue(new_user)
        self.assertEqual(new_user.email, "test_acl@pleio.nl")

        acl = { field.profile_field.guid: {
                'read_access': field.read_access,
                'write_access': field.write_access
             } for field in UserProfileField.objects.filter(user_profile=new_user.profile)}

        self.assertDictEqual(acl, {
            self.profile_field1.guid: {
                'read_access': ["user:{}".format(new_user.pk), "logged_in"],
                'write_access': ["user:{}".format(new_user.pk)]
            },
            self.profile_field_multiselect.guid: {
                'read_access': ["user:{}".format(new_user.pk), "logged_in"],
                'write_access': ["user:{}".format(new_user.pk)]
            },
            self.profile_field_datefield.guid: {
                'read_access': ["user:{}".format(new_user.pk), "logged_in"],
                'write_access': ["user:{}".format(new_user.pk)]
            },
        })

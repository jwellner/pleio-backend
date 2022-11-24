from core.models import ProfileField, ProfileSet
from core.tests.helpers import PleioTenantTestCase
from django.urls import reverse
from mixer.backend.django import mixer
from user.factories import AdminFactory


class TestAddProfilesetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory(is_superadmin=True)
        self.field = mixer.blend(ProfileField)

    def test_add_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('optional_features_add_profile_field'))
        self.assertEqual(200, response.status_code)

    def test_add_submit(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('optional_features_add_profile_field'), {
            'name': "test",
            'field': str(self.field.pk)
        })
        self.assertEqual(302, response.status_code)


class TestUpdateProfilesetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory(is_superadmin=True)
        self.field = mixer.blend(ProfileField)
        self.profile_set = ProfileSet.objects.create(
            name="Test",
            field=self.field,
        )
        self.EDIT_URL = reverse('optional_features_edit_profile_field', args=[self.profile_set.pk])
        self.DELETE_URL = reverse('optional_features_delete_profile_field', args=[self.profile_set.pk])

    def tearDown(self):
        self.admin.delete()
        self.field.delete()
        self.profile_set.delete()
        super().tearDown()

    def test_edit_anonymous(self):
        response = self.client.get(self.EDIT_URL)
        self.assertEqual(401, response.status_code)

    def test_edit_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.EDIT_URL)
        self.assertEqual(200, response.status_code)

    def test_edit_submit_form(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.EDIT_URL, {
            'name': 'new name',
            'field': str(self.field.pk),
        })
        self.assertEqual(302, response.status_code)
        self.profile_set.refresh_from_db()
        self.assertEqual(self.profile_set.name, 'new name')
        self.assertEqual(self.profile_set.field, self.field)

    def test_delete_anonymous(self):
        response = self.client.get(self.DELETE_URL)
        self.assertEqual(401, response.status_code)

    def test_delete_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.DELETE_URL)
        self.assertEqual(200, response.status_code)

    def test_post_delete_form(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.DELETE_URL, {'confirmed': 'true'})
        self.assertEqual(302, response.status_code)

        with self.assertRaises(ProfileSet.DoesNotExist):
            self.profile_set.refresh_from_db()

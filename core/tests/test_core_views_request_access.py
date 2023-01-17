from unittest import mock

from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory


class TestCoreViewsRequestAccessTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.claims = {
            "name": "John the Baptist",
            "email": "john@example.com",
        }

    def tearDown(self):
        self.admin.delete()

        super().tearDown()

    def test_start_request(self):
        self.update_session(request_access_claims=self.claims)

        response = self.client.get(reverse('request_access'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/request.html')

    @mock.patch("core.models.site.SiteAccessRequestManager.create")
    @mock.patch("core.views.schedule_site_access_request_mail")
    def test_post_request(self, schedule_site_access_request_mail, model_create):
        self.update_session(request_access_claims=self.claims)

        response = self.client.post(reverse('request_access'), data={
            'request_access': True,
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("access_requested"))
        self.assertEqual(schedule_site_access_request_mail.call_count, 1)
        self.assertEqual(model_create.call_count, 1)

    def test_without_claims(self):
        response = self.client.get(reverse('request_access'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


class TestCoreViewsAccessRequestedTestCase(PleioTenantTestCase):

    def test_access_requested_view(self):
        response = self.client.get(reverse("access_requested"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/requested.html')

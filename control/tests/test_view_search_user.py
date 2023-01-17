from http import HTTPStatus
from unittest import mock

from django.http import HttpResponse

from control.tests.helpers import Control as _


class TestViewSearchUserTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse('search_user'))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "search_user.html")

    def test_search_user_index_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse('search_user'))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "search_user.html")

    def test_search_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(_.reverse('search_user'), data={"email": self.admin.email})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "search_user.html")

    @mock.patch("control.views.render")
    @mock.patch("tenants.models.ClientManager.exclude")
    def test_search_known_user(self, manager_exclude, render):
        manager_exclude.return_value = [self.public_tenant]
        render.return_value = HttpResponse("Demo")

        self.client.force_login(self.admin)
        self.client.post(_.reverse('search_user'), data={"email": self.admin.email})

        request, template, context = render.call_args.args
        self.assertEqual(context['sites'], [{
            "schema": "public", "domain": self.public_tenant.primary_domain,
            "id": self.public_tenant.id,
            "user_email": self.admin.email,
            "user_external_id": None,
            "user_name": self.admin.name,
        }])

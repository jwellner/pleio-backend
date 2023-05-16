from http import HTTPStatus

from control.tests.helpers import Control as _
from core.tests.helpers import suppress_stdout
from tenants.models import Client


class TestViewSitesTestCase(_.BaseTestCase):

    @suppress_stdout()
    def setUp(self):
        super().setUp()
        self.demo, _ = Client.objects.get_or_create(schema_name="demo1")

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("sites"))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites.html")

    def test_normal_operation(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("sites"))
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites.html")
        self.assertIn(self.demo.schema_name, content.decode())

    def test_invalid_paginator(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("sites"), data={"page": "foo"})
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.demo.schema_name, content.decode())

    def test_paginator_overflow(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("sites"), data={"page": 100})
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.demo.schema_name, content.decode())

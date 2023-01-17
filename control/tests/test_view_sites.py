from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewSitesTestCase(_.BaseTestCase):

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
        self.assertIn("fast_test", content.decode())

    def test_invalid_paginator(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("sites"), data={"page": "foo"})
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("fast_test", content.decode())

    def test_paginator_overflow(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("sites"), data={"page": 100})
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("fast_test", content.decode())

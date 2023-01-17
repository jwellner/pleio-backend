from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewTasksTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("tasks"))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "tasks.html")

    def test_view_tasks(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("tasks"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "tasks.html")

    def test_view_tasks_invalid_paginator(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("tasks"), data={
            "page": "foo"
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "tasks.html")

    def test_view_tasks_out_of_range_paginator(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("tasks"), data={
            "page": 100
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "tasks.html")

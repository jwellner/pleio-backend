from http import HTTPStatus

from django.core.cache import cache
from django.db import connection

from tenants.helpers import FastTenantTestCase
from core.tests.helpers import override_config

class RobotsTxtTests(FastTenantTestCase):

    @override_config(ENABLE_SEARCH_ENGINE_INDEXING=True)
    def test_enabled_get(self):

        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")
        self.assertContains(response, "Sitemap:")

    @override_config(ENABLE_SEARCH_ENGINE_INDEXING=False)
    def test_disabled_get(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")
        self.assertEqual(lines[1], "Disallow: /")

    def test_post_disallowed(self):
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

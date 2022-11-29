from http import HTTPStatus

from django.core.cache import cache
from django.db import connection

from tenants.helpers import FastTenantTestCase


class RobotsTxtTests(FastTenantTestCase):

    def test_enabled_get(self):
        cache.set("%s%s" % (connection.schema_name, 'ENABLE_SEARCH_ENGINE_INDEXING'), True)

        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")
        self.assertContains(response, "Sitemap:")

    def test_disabled_get(self):
        cache.set("%s%s" % (connection.schema_name, 'ENABLE_SEARCH_ENGINE_INDEXING'), False)
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")
        self.assertEqual(lines[1], "Disallow: /")

    def test_post_disallowed(self):
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

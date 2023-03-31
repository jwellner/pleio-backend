import json

from django.core.exceptions import ValidationError

from core.utils.tiptap_parser import Tiptap
from tenants.helpers import FastTenantTestCase


class TiptapParserTestCase(FastTenantTestCase):

    def test_mentioned_users(self):
        user_id = 'c5617f63-6c98-44b5-a206-ff05eb648e52'
        tiptap_json = {
            'type': 'mention',
            'attrs': {
                'id': user_id,
                'label': 'Mr user',
            },
        }
        tiptap = Tiptap(tiptap_json)

        self.assertSetEqual(tiptap.mentioned_users, {user_id})

    def test_mentioned_users_duplicates(self):
        user_id = 'c5617f63-6c98-44b5-a206-ff05eb648e52'
        tiptap_json = {
            'type': 'doc',
            'content': [
                {
                    'type': 'mention',
                    'attrs': {
                        'id': user_id,
                        'label': 'Mr user',
                    },
                },
                {
                    'type': 'mention',
                    'attrs': {
                        'id': user_id,
                        'label': 'Mr user',
                    },
                }
            ]
        }
        tiptap = Tiptap(tiptap_json)

        self.assertSetEqual(tiptap.mentioned_users, {user_id})

    def test_mentioned_users_faulty(self):
        tiptap_json = {
            'type': 'mention',
            'attrs': {
                'label': 'Mr user',
            },
        }
        tiptap = Tiptap(tiptap_json)

        self.assertSetEqual(tiptap.mentioned_users, set())

    def test_mentioned_users_none(self):
        tiptap_json = {}
        tiptap = Tiptap(tiptap_json)

        self.assertSetEqual(tiptap.mentioned_users, set())

    def test_mentioned_users_string(self):
        user_id = 'c5617f63-6c98-44b5-a206-ff05eb648e52'
        tiptap_json = "{\"type\":\"doc\",\"content\":[{\"type\":\"paragraph\",\"attrs\":{\"intro\":false},\"content\":[{\"type\":\"mention\",\"attrs\":{\"id\":\"c5617f63-6c98-44b5-a206-ff05eb648e52\",\"label\":\"Kaj\"}},{\"type\":\"text\",\"text\":\" a\"}]}]}"
        tiptap = Tiptap(tiptap_json)

        self.assertSetEqual(tiptap.mentioned_users, {user_id})

    def test_replace_attachment(self):
        original = "111111"
        replacement = "99999999"
        tiptap_json = {
            'type': 'file',
            'attrs': {
                'url': original,
            },
        }
        tiptap = Tiptap(tiptap_json)

        tiptap.replace_attachment(original, replacement)
        result = tiptap.tiptap_json

        self.assertEqual(result['attrs']['url'], replacement)

    def test_replace_attachment_empty(self):
        original = ""
        replacement = "8888888"
        tiptap_json = {
            'type': 'file',
            'attrs': {
                'url': "1111111",
            },
        }
        tiptap = Tiptap(tiptap_json)

        tiptap.replace_attachment(original, replacement)
        result = tiptap.tiptap_json

        self.assertEqual(result['attrs']['url'], tiptap_json['attrs']['url'])

    def test_validate_rich_text_attachments_with_absolute_urls(self):
        file_json = json.dumps({"content": [
            {"type": "file", "attrs": {"url": "https://example.com"}}
        ]})
        image_json = json.dumps({"content": [
            {"type": "image", "attrs": {"src": "https://example.com"}}
        ]})

        with self.assertRaises(ValidationError):
            Tiptap(file_json).check_for_external_urls()

        with self.assertRaises(ValidationError):
            Tiptap(image_json).check_for_external_urls()

    def test_validate_rich_text_attachments_with_relative_urls(self):
        file_json = json.dumps({"content": [
            {"type": "file", "attrs": {"url": "/foo/bar"}}
        ]})
        image_json = json.dumps({"content": [
            {"type": "image", "attrs": {"src": "no/path/prefix"}}
        ]})
        file_json_localdomain = json.dumps({"content": [
            {"type": "file", "attrs": {"url": "https://tenant.fast-test.com/foo/bar"}}
        ]})
        image_json_localdomain = json.dumps({"content": [
            {"type": "image", "attrs": {"src": "http://tenant.fast-test.com/no/path/prefix"}}
        ]})

        # Expect no ValidationErrors being raised
        Tiptap(file_json).check_for_external_urls()
        Tiptap(image_json).check_for_external_urls()
        Tiptap(file_json_localdomain).check_for_external_urls()
        Tiptap(image_json_localdomain).check_for_external_urls()

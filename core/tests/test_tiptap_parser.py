from core.utils.tiptap_parser import Tiptap
from django_tenants.test.cases import FastTenantTestCase

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

import json
from django_tenants.test.cases import FastTenantTestCase
from core.utils.convert import is_tiptap, is_draft, tiptap_to_text, tiptap_to_html, draft_to_tiptap

class UtilsTestCase(FastTenantTestCase):

    def setUp(self):

        self.tiptap_json = {
            'type': 'doc',
            'content': [
                {
                    'type': 'paragraph',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Dit is een '
                        },
                        {
                            'type': 'text',
                            'text': 'paragraph',
                            'marks': [{'type': 'bold'}],
                        }
                    ]
                }
            ]
        }

        self.draft_json = {
            "blocks": [
                {
                    "key": "1234",
                    "text": "Dit is een paragraph",
                    "type": "paragraph",
                    "entityRanges": [],
                    "inlineStyleRanges": [{
                        "offset": 11,
                        "length": 9,
                        "style": "BOLD"
                    }],
                    "depth": 0,
                    "data": {}
                }
            ],
            "entityMap": {}
        }

    def tearDown(self):
        pass

    def test_is_tiptap(self):
        self.assertTrue(is_tiptap(json.dumps(self.tiptap_json)))
        self.assertFalse(is_tiptap(json.dumps(self.draft_json)))

    def test_is_draft(self):
        self.assertTrue(is_draft(json.dumps(self.draft_json)))
        self.assertFalse(is_draft(json.dumps(self.tiptap_json)))

    def test_tiptap_to_text(self):
        result = tiptap_to_text(json.dumps(self.tiptap_json))
        self.assertIn("Dit is een paragraph", result)

    def test_tiptap_to_text_with_mention(self):
        tiptap = {
            'type': 'doc',
            'content': [
                {
                    'type': 'mention',
                    'attrs': {
                        'id': '1234-1234-1234-12',
                        'label': 'user X'
                    },
                }
            ],
        }

        result = tiptap_to_text(json.dumps(tiptap))

        self.assertIn("user X", result)


    def test_tiptap_to_html(self):
        result = tiptap_to_html(json.dumps(self.tiptap_json))
        self.assertIn("<p>Dit is een <strong>paragraph</strong></p>", result)

    def test_draft_to_tiptap(self):
        result = json.loads(draft_to_tiptap(json.dumps(self.draft_json)))
        self.assertEqual(result, self.tiptap_json)

import json

from core.utils.convert import is_tiptap, tiptap_to_text, tiptap_to_html

from django_tenants.test.cases import FastTenantTestCase


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

    def test_blockquote_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'blockquote',
                'content': [{
                    'type': "paragraph",
                    'content': [{
                        'type': 'text',
                        'text': 'expected blockquote',
                    }]
                }]
            }]
        })
        self.assertEqual("<blockquote><p>expected blockquote</p></blockquote>", tiptap_to_html(spec))

    def test_heading_to_html(self):
        for n in [1, 2, 3, 4, 5, 6]:
            spec = json.dumps({
                'type': 'doc',
                'content': [
                    {
                        'type': 'heading',
                        'attrs': {'level': n},
                        'content': [{
                            'type': 'text',
                            'text': 'expected header',
                        }]
                    }
                ]
            })
            self.assertEqual("<h{n}>expected header</h{n}>".format(n=n), tiptap_to_html(spec))

    def test_text_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [
                {
                    'type': 'text',
                    'text': 'expected text'
                }
            ]
        })
        self.assertEqual("expected text", tiptap_to_html(spec))

    def test_image_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [
                {
                    'type': 'image',
                    'attrs': {'src': 'path/to/image',
                              'alt': 'expected-alt',
                              'title': 'expected-title',
                              'size': 'expected-size',
                              'caption': 'expected-caption'}
                }
            ]
        })
        self.assertEqual('<img'
                         ' src="path/to/image"'
                         ' alt="expected-alt"'
                         ' title="expected-title"'
                         ' size="expected-size"'
                         ' caption="expected-caption"'
                         '>',
                         tiptap_to_html(spec))

    def test_figure_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [
                {
                    'type': 'figure',
                    'attrs': {'src': 'path/to/figure',
                              'alt': 'expected-alt',
                              'title': 'expected-title',
                              'size': 'expected-size',
                              'caption': 'expected-caption'}
                }
            ]
        })
        self.assertEqual('<img'
                         ' src="path/to/figure"'
                         ' alt="expected-alt"'
                         ' title="expected-title"'
                         ' size="expected-size"'
                         ' caption="expected-caption"'
                         '>', tiptap_to_html(spec))

    def test_file_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'file',
                'attrs': {
                    'name': 'expected-name',
                    'url': 'path/to/file',
                    'mimeType': 'x-test',
                    'size': 'expected-size'
                }
            }]
        })
        self.assertEqual('<a href="path/to/file">expected-name</a>', tiptap_to_html(spec))

    def test_video_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'video',
                'attrs': {
                    'guid': 'expeced-guid',
                    'title': 'expeced-title',
                    'platform': 'path/to/content'
                }
            }]
        })
        self.assertEqual('<iframe src="path/to/content"></iframe>', tiptap_to_html(spec))

    def test_hardBreak_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'hardBreak',
            }]
        })
        self.assertEqual('<br>', tiptap_to_html(spec))

    def test_bulletList_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'bulletList',
                'content': [{
                    'type': 'listItem',
                    'content': [{
                        'type': 'text',
                        'text': 'List item'
                    }]
                }]
            }]
        })
        self.assertEqual('<ul><li>List item</li></ul>', tiptap_to_html(spec))

    def test_orderedList_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [{
                'type': 'orderedList',
                'content': [{
                    'type': 'listItem',
                    'content': [{
                        'type': 'text',
                        'text': 'List item'
                    }]
                }]
            }]
        })
        self.assertEqual('<ol><li>List item</li></ol>', tiptap_to_html(spec))

    def test_table_to_html(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [
                {
                    'type': 'table',
                    'content': [
                        {'type': 'tableRow',
                         'content': [
                             {'type': 'tableHeader',
                              'content': [{'type': 'text', 'text': 'Column 1'}]
                              },
                             {'type': 'tableHeader',
                              'content': [{'type': 'text', 'text': 'Column 2'}]
                              },
                         ]},
                        {'type': 'tableRow',
                         'content': [
                             {'type': 'tableCell',
                              'content': [{'type': 'text', 'text': 'Value 1'}]
                              },
                             {'type': 'tableCell',
                              'content': [{'type': 'text', 'text': 'Value 2'}]
                              }
                         ]},
                    ]
                }
            ]
        })
        self.assertEqual('<table>'
                         '<tr><th>Column 1</th><th>Column 2</th></tr>'
                         '<tr><td>Value 1</td><td>Value 2</td></tr>'
                         '</table>', tiptap_to_html(spec))

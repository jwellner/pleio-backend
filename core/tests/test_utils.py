import json
from unittest import mock
import os.path

from core.tests.helpers import PleioTenantTestCase
from core.utils.convert import is_tiptap, tiptap_to_text, tiptap_to_html
from core.utils.export import fetch_avatar_image, CouldNotLoadPictureError
from user.factories import UserFactory


from core.utils.export import compress_path


class TestUtilsTipTapIOTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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

    def test_is_tiptap(self):
        # Has tiptapjson
        # Has draftjson
        self.assertTrue(is_tiptap(json.dumps(self.tiptap_json)))
        self.assertFalse(is_tiptap(json.dumps(self.draft_json)))

    def test_tiptap_to_text(self):
        # Has tiptapjson
        result = tiptap_to_text(json.dumps(self.tiptap_json))
        self.assertIn("Dit is een paragraph", result)

    def test_tiptap_to_html(self):
        # Has tiptapjson
        result = tiptap_to_html(json.dumps(self.tiptap_json))
        self.assertIn("<p>Dit is een <strong>paragraph</strong></p>", result)

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

    def test_table_with_lists(self):
        spec = json.dumps({
            'type': 'doc',
            'content': [
                {'type': 'table',
                 'content': [
                     {'type': 'tableRow',
                      'content': [
                          {'type': 'tableCell',
                           'content': [
                               {'type': 'bulletList',
                                'content': [
                                    {'type': 'listItem',
                                     'content': [
                                         {'type': 'text', 'text': 'Bullet list item'}
                                     ]}
                                ]},
                           ]},
                      ]},
                     {'type': 'tableRow',
                      'content': [
                          {'type': 'tableCell',
                           'content': [
                               {'type': 'orderedList',
                                'content': [
                                    {'type': 'listItem',
                                     'content': [
                                         {'type': 'text', 'text': 'Ordered list item'}
                                     ]}
                                ]},
                           ]},
                      ]},
                 ]}
            ]
        })
        self.assertEqual('<table>'
                         '<tr><td><ul><li>Bullet list item</li></ul></td></tr>'
                         '<tr><td><ol><li>Ordered list item</li></ol></td></tr>'
                         '</table>', tiptap_to_html(spec))


class TestFetchAvatarTestCase(PleioTenantTestCase):
    PICTURE_URL = 'https://picture.jpg'
    THUMBNAIL_URL = 'https://thumbnail.jpg'
    ORIGINAL_URL = 'https://original.jpg'

    def setUp(self):
        from requests import Response
        super().setUp()
        self.user = UserFactory(picture=self.PICTURE_URL)
        self.response = mock.MagicMock(spec=Response)
        self.response.ok = True
        self.response.content = open(self.relative_path(__file__, ['assets', 'avatar.jpg']), 'rb').read()
        self.response.headers = {"content-type": "image/jpeg"}

    @mock.patch("core.utils.export.fetch_avatar")
    @mock.patch("core.utils.export.requests.get")
    def test_fetch_avatar_with_external_original_url(self, mocked_get, mocked_get_data):
        mocked_get_data.return_value = {'originalAvatarUrl': self.ORIGINAL_URL,
                                        'avatarUrl': self.THUMBNAIL_URL}
        mocked_get.return_value = self.response

        response = fetch_avatar_image(self.user)

        self.assertTrue(mocked_get.called)
        self.assertEqual(mocked_get.call_args.args, (self.ORIGINAL_URL,))
        self.assertEqual((self.response.content, '.jpg'), response)

    @mock.patch("core.utils.export.fetch_avatar")
    @mock.patch("core.utils.export.requests.get")
    def test_fetch_avatar_with_external_thumbnail_only(self, mocked_get, mocked_get_data):
        mocked_get_data.return_value = {'avatarUrl': self.THUMBNAIL_URL}
        mocked_get.return_value = self.response

        with self.assertRaises(CouldNotLoadPictureError):
            fetch_avatar_image(self.user)

        self.assertFalse(mocked_get.called)

    @mock.patch("core.utils.export.fetch_avatar")
    @mock.patch("core.utils.export.requests.get")
    def test_fetch_avatar_without_external_urls(self, mocked_get, mocked_get_data):
        mocked_get_data.return_value = {}
        mocked_get.return_value = self.response

        with self.assertRaises(CouldNotLoadPictureError):
            fetch_avatar_image(self.user)

        self.assertFalse(mocked_get.called)

    @mock.patch("core.utils.export.fetch_avatar")
    @mock.patch("core.utils.export.requests.get")
    def test_fetch_avatar_with_error(self, mocked_get, mocked_get_data):
        mocked_get_data.return_value = {'error': 'some error message'}
        mocked_get.return_value = self.response

        with self.assertRaises(CouldNotLoadPictureError):
            fetch_avatar_image(self.user)

        self.assertFalse(mocked_get.called)

    @mock.patch("core.utils.export.fetch_avatar")
    @mock.patch("core.utils.export.requests.get")
    def test_fetch_avatar_without_any_url(self, mocked_get, mocked_get_data):
        self.user.picture = ''
        self.user.save()
        mocked_get_data.return_value = {'originalAvatarUrl': None,
                                        'avatarUrl': None}

        with self.assertRaises(CouldNotLoadPictureError):
            fetch_avatar_image(self.user)

        self.assertFalse(mocked_get.called)


class TestUtilsCompressPathTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.base_file = self.file_factory(self.relative_path(__file__, ['assets', 'text_file.txt']))

    def test_correctly_created_zip_object(self):
        zipfile = None
        try:
            zipfile = compress_path(self.base_file.upload.path)
            self.assertTrue(os.path.exists(zipfile))
        finally:
            if zipfile and os.path.exists(zipfile):
                os.unlink(zipfile)

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile

from core.lib import get_full_url, replace_html_img_src
from core.models import Attachment
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestLibReplaceHtmlImageSrc(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.visitor = UserFactory()

    def tearDown(self):
        self.visitor.delete()
        super().tearDown()

    def test_replace_html_img_src_html(self):
        expected_url = '/path/to/image.jpg'
        html = f"""<div>
        <img src="{expected_url}">
        </div>"""
        self.assertIn(expected_url, html)
        self.assertNotIn(get_full_url(expected_url), html)

        result = replace_html_img_src(html, user=self.visitor, file_type='html')

        self.assertIn(expected_url, result)
        self.assertIn(get_full_url(expected_url), result)

    def test_replace_html_img_odt(self):
        attachment = Attachment.objects.create(name='Demo.jpg',
                                               owner=self.visitor,
                                               upload=ContentFile("Content...", 'Demo.jpg'))
        expected_url = '/attachment/' + attachment.guid
        html = f"""<div>
        <img src="{expected_url}">
        </div>"""
        self.assertIn(expected_url, html)
        self.assertNotIn(attachment.upload.path, html)

        result = replace_html_img_src(html, user=self.visitor, file_type='odt')

        self.assertNotIn(expected_url, result)
        self.assertIn(attachment.upload.path, result)

    def test_replace_html_img_anonymous_odt(self):
        attachment = Attachment.objects.create(name='Demo.jpg',
                                               owner=self.visitor,
                                               upload=ContentFile("Content...", 'Demo.jpg'))
        expected_url = '/attachment/' + attachment.guid
        html = f"""<div>
        <img src="{expected_url}">
        </div>"""
        self.assertIn(expected_url, html)
        self.assertNotIn(attachment.upload.path, html)

        result = replace_html_img_src(html, user=AnonymousUser(), file_type='odt')

        self.assertIn(expected_url, result)
        self.assertNotIn(attachment.upload.path, result)

    def test_replace_not_attachment_img_odt(self):
        expected_url = '/path/to/image.jpg'
        html = f"""<div>
        <img src="{expected_url}">
        </div>"""
        self.assertIn(expected_url, html)

        result = replace_html_img_src(html, user=self.visitor, file_type='odt')

        self.assertIn(expected_url, result)

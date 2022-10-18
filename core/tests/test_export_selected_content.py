import io
from http import HTTPStatus
from zipfile import ZipFile

from django_tenants.test.client import TenantClient
from mixer.backend.django import mixer

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from event.models import Event
from user.factories import AdminFactory, UserFactory
from wiki.models import Wiki


class TestExportSelectedContentTestCase(PleioTenantTestCase):
    
    def setUp(self):
        super(TestExportSelectedContentTestCase, self).setUp()

        self.admin = AdminFactory()
        self.user1 = UserFactory()
        self.blog1 = mixer.blend(Blog)
        self.blog2 = mixer.blend(Blog)
        self.event = mixer.blend(Event)
        self.wiki = mixer.blend(Wiki)

    def test_export_selected_content(self):

        self.client.force_login(self.admin)

        path = '/exporting/content/selected?content_guids[]={}&content_guids[]={}&content_guids[]={}'.format(self.blog1.id, self.blog2.id, self.event.id)
        response = self.client.get(path)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        zip_file = io.BytesIO(b''.join(response.streaming_content))

        with ZipFile(zip_file, 'r') as zip:
            names = zip.namelist()
            self.assertEqual(names[0], 'blog-export.csv')
            self.assertEqual(names[1], 'event-export.csv')

    def test_export_selected_content_anonymous(self):
        path = '/exporting/content/selected?content_guids[]={}&content_guids[]={}&content_guids[]={}'.format(self.blog1.id, self.blog2.id, self.event.id)
        response = self.client.get(path)

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

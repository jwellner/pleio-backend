import io
from http import HTTPStatus
from zipfile import ZipFile

from mixer.backend.django import mixer

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase, override_config
from event.models import Event
from user.factories import AdminFactory, UserFactory
from wiki.models import Wiki


class TestExportSelectedContentTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.user1 = UserFactory()
        self.blog1 = mixer.blend(Blog)
        self.blog2 = mixer.blend(Blog)
        self.event = mixer.blend(Event)
        self.wiki = mixer.blend(Wiki)

        self.selection = '/exporting/content/selected?content_guids[]={}&content_guids[]={}&content_guids[]={}'.format(self.blog1.id, self.blog2.id,
                                                                                                                       self.event.id)

    def tearDown(self):
        super().tearDown()

    def test_export_selected_content(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.selection)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        zip_file = io.BytesIO(response.getvalue())

        with ZipFile(zip_file, 'r') as fh:
            names = fh.namelist()
            self.assertEqual(names[0], 'blog-export.csv')
            self.assertEqual(names[1], 'event-export.csv')

    @override_config(IS_CLOSED=False)
    def test_export_selected_content_anonymous(self):
        response = self.client.get(self.selection)

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTemplateUsed("react.html")

    @override_config(IS_CLOSED=False)
    def test_export_selected_content_as_visitor(self):
        self.client.force_login(self.user1)

        response = self.client.get(self.selection)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateUsed("react.html")

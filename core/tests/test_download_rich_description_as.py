from http import HTTPStatus


from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django.test import override_settings
from user.models import User
from core.models.group import Group
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class DownloadRichDescriptionAsTestCase(TenantTestCase):

    def setUp(self):
        super(DownloadRichDescriptionAsTestCase, self).setUp()
        self.c = TenantClient(self.tenant)
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedAdminUser = mixer.blend(User, roles = ['ADMIN'])
        self.group = mixer.blend(Group, owner=self.authenticatedAdminUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'member')

        self.pad = FileFolder.objects.create(
            type=FileFolder.Types.PAD,
            title="Test group pad",
            rich_description="JSON to string. text",
            group=self.group,
            read_access=[ACCESS_TYPE.group.format(self.group.id)],
            write_access=[ACCESS_TYPE.group.format(self.group.id)],
            owner=self.authenticatedAdminUser
        )

    def tearDown(self):
        self.pad.delete()
        self.authenticatedUser.delete()
        self.authenticatedAdminUser.delete()

    def test_download_rich_description_as_html(self):

        path = '/download_rich_description_as/' + str(self.pad.id) + '/html'
        self.c.force_login(self.authenticatedUser)
        response = self.c.get(path)
       
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(b'JSON to string. text\n', b''.join(response.streaming_content))

    def test_download_rich_description_as_odt(self):

        path = '/download_rich_description_as/' + str(self.pad.id) + '/odt'
        self.c.force_login(self.authenticatedUser)
        response = self.c.get(path)
      
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @override_settings(DEBUG=False)
    def test_download_rich_description_as_not_supported_file_type(self):

        path = '/download_rich_description_as/' + str(self.pad.id) + '/notexisting'
        self.c.force_login(self.authenticatedUser)
        response = self.c.get(path)
       
        self.assertTemplateUsed(response, 'react.html')
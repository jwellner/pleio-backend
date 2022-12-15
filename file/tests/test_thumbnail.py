from http import HTTPStatus
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from file.models import FileFolder
from core.constances import ACCESS_TYPE

class ThumbnailTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ThumbnailTestCase, self).setUp()

        self.user = UserFactory()

        upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'grass.jpg']))

        self.file = FileFolder.objects.create(
            owner=self.user,
            upload=upload,
            type=FileFolder.Types.FILE,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)]
        )

    def test_thumbnail_anonymous(self):
        response = self.client.get("/file/thumbnail/{}".format(self.file.id))
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_thumbnail(self):
        self.client.force_login(self.user)
        response = self.client.get("/file/thumbnail/{}".format(self.file.id))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
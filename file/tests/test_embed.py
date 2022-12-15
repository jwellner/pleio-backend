from http import HTTPStatus

from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory

from ..models import FileFolder


class EmbedTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EmbedTestCase, self).setUp()

        self.user = UserFactory()
        self.user2 = UserFactory()
        self.group = mixer.blend(Group, is_closed=True, owner=self.user)
        self.group.join(self.user)

        upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'upload.txt']))

        self.file = FileFolder.objects.create(
            owner=self.user,
            upload=upload,
            group=self.group,
            type=FileFolder.Types.FILE,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user.id)]
        )

    def test_embed_anonymous(self):
        response = self.client.get("/file/embed/{}".format(self.file.id))
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_embed_not_in_group(self):
        self.client.force_login(self.user2)
        response = self.client.get("/file/embed/{}".format(self.file.id))
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_embed(self):
        self.client.force_login(self.user)
        response = self.client.get("/file/embed/{}".format(self.file.id))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(list(response.streaming_content), "Demo upload file.")
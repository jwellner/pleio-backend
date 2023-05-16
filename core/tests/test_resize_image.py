from io import BytesIO
from unittest import mock

from PIL import Image
from django.core.files.base import ContentFile
from mixer.backend.django import mixer

from core.models.image import ResizedImage
from core.tasks import image_resize
from core.tests.helpers import PleioTenantTestCase, override_config
from file.factories import FileFactory
from user.models import User


class ResizeImageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = mixer.blend(User)

    def get_image(self, filename, size=(800, 1280)):
        output = BytesIO()
        img = Image.new("RGB", size, (255, 255, 255))
        img.save(output, "JPEG")

        contents = output.getvalue()

        return ContentFile(contents, filename)

    @override_config(IS_CLOSED=False)
    @mock.patch('celery.current_app.send_task')
    def test_redirect(self, mock_send_task):
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image("some-image.jpg"))
        response = self.client.get(attachment.attachment_url + "?size=414", follow=True)

        mock_send_task.assert_called_once()
        self.assertRedirects(response, attachment.attachment_url)

    @override_config(IS_CLOSED=False)
    @mock.patch('celery.current_app.send_task')
    def test_resize_resolve(self, mock_send_task):
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image("some-image.jpg"))
        ResizedImage.objects.create(
            original=attachment,
            size=414,
            upload=self.get_image('testfile2.jpg'),
            status='OK'
        )

        response = self.client.get(attachment.url + "?size=414")
        mock_send_task.assert_not_called()

        self.assertEqual(response.status_code, 200)

    @override_config(IS_CLOSED=False)
    def test_resize_square(self):
        size = 414
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image("some-image.jpg", size=(1000, 1000)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.width, size)
        self.assertEqual(resized.height, size)

    @override_config(IS_CLOSED=False)
    def test_resize_small(self):
        size = 414
        height = 10
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image('testfile.jpg', size=(1000, height)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.height, height)

    @override_config(IS_CLOSED=False)
    def test_resize_vertical(self):
        size = 414
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image('testfile.jpg', size=(800, 1000)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.width, size)

    @override_config(IS_CLOSED=False)
    def test_resize_horizontal(self):
        size = 414
        attachment = FileFactory(owner=self.authenticatedUser,
                                 upload=self.get_image('testfile.jpg', size=(1000, 800)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.height, size)

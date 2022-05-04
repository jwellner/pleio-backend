from celery import shared_task
from django.utils import timezone
from django.utils.timezone import timedelta
from django_tenants.utils import schema_context

from core.lib import tenant_schema
from file.models import FileFolder


def cleanup_featured_image_files(imageField):
    if not imageField:
        return

    delay = timezone.now() + timedelta(seconds=30)
    do_cleanup_featured_image_files.apply_async(args=(tenant_schema(),
                                                      imageField.id),
                                                eta=delay)


@shared_task
def do_cleanup_featured_image_files(schema_name, imageFileId):
    try:
        with schema_context(schema_name):
            imageFile = FileFolder.objects.get(id=imageFileId)
            imageFile.resized_images.all().delete()
            imageFile.delete()
    except FileFolder.DoesNotExist:
        pass

from celery import shared_task
from django.utils import timezone
from django.utils.timezone import timedelta
from django_tenants.utils import schema_context

from core.lib import tenant_schema


def cleanup_featured_image_files(image_guid):
    if not image_guid:
        return

    delay = timezone.now() + timedelta(seconds=30)
    do_cleanup_featured_image_files.apply_async(args=(tenant_schema(),
                                                      image_guid),
                                                eta=delay)


@shared_task
def do_cleanup_featured_image_files(schema_name, image_guid):
    # pylint: disable=import-outside-toplevel
    from file.models import FileFolder
    try:
        with schema_context(schema_name):
            imageFile = FileFolder.objects.get(id=image_guid)
            imageFile.resized_images.all().delete()
            imageFile.delete()
    except FileFolder.DoesNotExist:
        pass

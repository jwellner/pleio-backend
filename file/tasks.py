# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.utils.log import get_task_logger
from django_tenants.utils import schema_context
from file.models import FileFolder
from file.helpers import resize_and_update_image

logger = get_task_logger(__name__)

@shared_task(bind=True, ignore_result=True)
def resize_featured(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    '''
    Resize featured image for tenant
    '''
    with schema_context(schema_name):
        try:
            image = FileFolder.objects.get(id=file_guid)
            resize_and_update_image(image, 1200, 2000)
        except Exception as e:
            logger.error('resize_featured %s %s: %s', schema_name, file_guid, e)

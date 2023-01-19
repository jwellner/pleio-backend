from celery import shared_task
from celery.utils.log import get_task_logger
from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.db_mutex import db_mutex
from django_tenants.utils import schema_context

from external_content.models import ExternalContentSource

logger = get_task_logger(__name__)


@shared_task
def fetch_external_content(schema_name):
    with schema_context(schema_name):
        for ecs in ExternalContentSource.objects.all():
            fetch_external_content_from_source.delay(schema_name, ecs.guid)


@shared_task
def fetch_external_content_from_source(schema_name, ecs_id):
    with schema_context(schema_name):
        lock_id = "%s:external_content:fetch_external_content_from_source:%s" % (schema_name, ecs_id)
        try:
            with db_mutex(lock_id):
                source = ExternalContentSource.objects.get(id=ecs_id)
                source.pull()
        except DBMutexError:
            logger.info("%s still busy", lock_id)
        except DBMutexTimeoutError:
            logger.error("%s timed out", lock_id)

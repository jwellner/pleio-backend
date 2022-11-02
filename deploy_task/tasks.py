from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils.module_loading import import_string
from django_tenants.utils import schema_context
from tenants.models import Client

logger = get_task_logger(__name__)


@shared_task
def schedule_deploy_task_for_all(method_name):
    for tenant in Client.objects.exclude(schema_name='public'):
        execute_deploy_task.delay(tenant.schema_name, method_name)


@shared_task
def execute_deploy_task(schema_name, method_name):
    with schema_context(schema_name):
        try:
            logger.error("execute_deploy_task start @%s %s", schema_name, method_name)
            method = import_string(method_name)
            method()
        except Exception as e:
            error_message = f"{e.__class__.__module__}.{e.__class__.__qualname__}: {e}"
            logger.error("execute_deploy_task error @%s %s %s", schema_name, method_name, error_message)
        finally:
            logger.error("execute_deploy_task end @%s %s", schema_name, method_name)

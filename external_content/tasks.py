from celery import shared_task
from django_tenants.utils import schema_context

from external_content.models import ExternalContentSource


@shared_task
def fetch_external_content(schema_name):
    with schema_context(schema_name):
        for ecs in ExternalContentSource.objects.all():
            fetch_external_content_from_source.delay(schema_name, ecs.guid)


@shared_task
def fetch_external_content_from_source(schema_name, ecs_id):
    with schema_context(schema_name):
        source = ExternalContentSource.objects.get(id=ecs_id)
        source.pull()

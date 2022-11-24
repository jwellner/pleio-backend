from celery import shared_task
from django_tenants.utils import schema_context


@shared_task
def update_post_deploy_tasks(schema_name):
    with schema_context(schema_name):
        from post_deploy.utils import skip_all_tasks
        skip_all_tasks("New tenant")

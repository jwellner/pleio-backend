from celery import shared_task
from celery.utils.log import get_task_logger
from django_tenants.utils import schema_context
from post_deploy import post_deploy_action

from activity.models import StatusUpdate
from blog.models import Blog
from core.lib import is_schema_public, tenant_schema
from core.models import AttachmentMixin
from core.utils.entity import load_entity_by_id, EntityNotFoundError
from discussion.models import Discussion
from news.models import News
from question.models import Question
from task.models import Task
from wiki.models import Wiki

logger = get_task_logger(__name__)


def _applicable_entities():
    models = (StatusUpdate,
              Blog,
              Discussion,
              News,
              Question,
              Task,
              Wiki)
    for model in models:
        instances = model.objects.filter(group__isnull=False).filter(rich_description__contains='file')
        for pk in instances.values_list('pk', flat=True):
            yield str(pk)


@post_deploy_action
def fix_unreferenced_group_files_used_as_attachments():
    if is_schema_public():
        return

    total = -1
    for total, guid in enumerate(_applicable_entities()):
        update_entity.delay(tenant_schema(), guid)

    logger.info("%s scheduled %s entities to be checked for attachments", tenant_schema(), total + 1)


@shared_task(rate_limit='100/m')
def update_entity(schema_name, guid):
    with schema_context(schema_name):
        try:
            entity = load_entity_by_id(guid, ['core.Entity'])
            if not isinstance(entity, AttachmentMixin) and 'file' in entity.rich_description:
                return
            logger.info("update_attachment_links for %s", entity.pk)
            entity.update_attachments_links()
        except EntityNotFoundError:
            pass

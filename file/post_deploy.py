from django.db.models import Q
from post_deploy import post_deploy_action

from core.lib import tenant_schema, is_schema_public
from file.models import FileFolder


@post_deploy_action
def fix_broken_filenames():
    # pylint: disable=unsupported-binary-operation
    if is_schema_public():
        return

    retry_files = FileFolder.objects.filter(Q(title__isnull=True)
                                            | Q(title__startswith='/')
                                            | Q(mime_type__isnull=True)
                                            | Q(size__lt=1)).filter(type=FileFolder.Types.FILE)

    for file in retry_files:
        from file.tasks import post_process_file_attributes
        post_process_file_attributes.delay(tenant_schema(), str(file.id))

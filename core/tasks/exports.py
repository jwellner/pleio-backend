from celery import shared_task
from django.core.files.base import ContentFile
from django_tenants.utils import schema_context

from core.constances import ACCESS_TYPE
from core.models import AvatarExport
from file.models import FileFolder


@shared_task
def export_avatars(schema, avatar_export_id):
    from core.utils.export import build_avatar_export
    from core.mail_builders.avatar_export_ready import schedule_avatar_export_ready_mail
    with schema_context(schema):
        AvatarExport.objects.filter(id=avatar_export_id).update(status='in_progress')
        avatar_export = AvatarExport.objects.get(id=avatar_export_id)

        zip_file_contents = build_avatar_export(avatar_export.initiator)

        avatar_export.file = FileFolder.objects.create(
            type=FileFolder.Types.FILE,
            owner=avatar_export.initiator,
            upload=ContentFile(zip_file_contents, 'avatar_export.zip'),
            read_access=[ACCESS_TYPE.user.format(avatar_export.initiator.guid)],
            write_access=[ACCESS_TYPE.user.format(avatar_export.initiator.guid)],
        )

        avatar_export.status = 'ready'
        avatar_export.save()

        schedule_avatar_export_ready_mail(avatar_export)





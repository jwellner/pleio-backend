from celery import shared_task
from django.core.files.base import ContentFile
from django.utils.timezone import localtime
from django_tenants.utils import schema_context

from core.constances import ACCESS_TYPE
from file.models import FileFolder


@shared_task
def export_avatars(schema, avatar_export_id):
    from core.mail_builders.avatar_export_ready import schedule_avatar_export_ready_mail
    from core.models import AvatarExport
    from core.utils.export.avatar import build_avatar_export

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


@shared_task
def export_my_content(schema, user_guid):
    from core.utils.export.content import ContentSnapshot
    with schema_context(schema):
        date = localtime()
        snapshot = ContentSnapshot(user_guid)
        file_object = FileFolder.objects.create(
            type=FileFolder.Types.FILE,
            tags=[ContentSnapshot.EXCLUDE_TAG],
            owner_id=user_guid,
            upload=ContentFile(snapshot.collect_content(), 'content-%s.zip' % date.strftime("%Y%m%d-%H%M")),
            read_access=[ACCESS_TYPE.user.format(user_guid)],
            write_access=[ACCESS_TYPE.user.format(user_guid)],
        )

        from core.mail_builders.content_export_ready import schedule_content_export_ready_mail
        schedule_content_export_ready_mail(file_object, file_object.owner)

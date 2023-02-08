from celery import chain
from django.utils import timezone
from django.utils.text import slugify


def schedule_backup(site, actor, include_files, create_archive):
    from control.tasks import backup_site, followup_backup_complete
    task_spec = chain(backup_site.s(site.id,
                                    skip_files=not bool(include_files),
                                    backup_folder=_backup_folder(site.schema_name),
                                    compress=bool(create_archive)),
                      followup_backup_complete.s(site.id,
                                                 actor.guid))
    return task_spec.apply_async()


def _backup_folder(schema_name):
    return slugify("%s_%s" % (
        timezone.localtime().strftime("%Y%m%d%H%M%S"),
        schema_name,
    ))

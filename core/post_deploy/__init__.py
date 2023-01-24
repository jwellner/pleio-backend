import csv
import os
import pandas as pd
import datetime

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Prefetch
from post_deploy import post_deploy_action

from core.lib import tenant_schema, is_schema_public, get_full_url
from notifications.models import Notification

from .migrate_rows_cols_widgets import deploy_action as migrate_rows_cols_widgets

logger = get_task_logger(__name__)


@post_deploy_action(auto=False)
def remove_notifications_with_broken_relation():
    if is_schema_public():
        return

    count = 0

    queryset = Notification.objects.prefetch_related(Prefetch('action_object'))

    for notification in queryset.iterator(chunk_size=10000):  # using iterator for large datasets memory consumption
        if not notification.action_object:
            notification.delete()
            count += 1

    logger.info("Deleted %s broken notifications", count)


@post_deploy_action
def write_missing_file_report():
    if is_schema_public():
        return

    from file.models import FileFolder
    report_file = os.path.join(settings.BACKUP_PATH, "missing_file_report_" + tenant_schema()) + '.csv'
    total = 0
    files_ok = 0
    files_err = 0
    with open(report_file, 'w') as fh:
        writer = csv.writer(fh, delimiter=';')
        writer.writerow(['id', 'path', 'url', 'name', 'owner', 'group', 'groupowner', 'groupownermail'])
        for file in FileFolder.objects.filter(type=FileFolder.Types.FILE, upload__isnull=False):
            try:
                if not os.path.exists(file.upload.path):
                    writer.writerow([
                        file.guid,
                        file.upload.path,
                        get_full_url(file.url),
                        file.title,
                        file.owner.name if file.owner else '-',
                        file.group.name if file.group else '-',
                        file.group.owner.name if file.group else '-',
                        file.group.owner.email if file.group else '-',
                    ])
                    total += 1
                else:
                    files_ok += 1
            except Exception as e:
                writer.writerow([
                    file.guid,
                    f"Error: {e.__class__} {e}",
                    file.owner.name if file.owner else '',
                    file.group.name if file.group else '',
                    file.group.owner.name if file.group else '',
                    file.group.owner.email if file.group else '',
                ])
                total += 1
                files_err += 1
        writer.writerow([f"{total} files can't be found on the disk."])
        writer.writerow([f"{files_ok} files were just fine."])
        writer.writerow([f"{files_err} files had errors while checking."])

    if total == 0:
        os.unlink(report_file)


@post_deploy_action
def entity_updated_at_from_report():
    """
    Fix updated_at date for entities involved in the 27/10/2022 updated_at incident
    Entity CSV format: id;updated_at
    """
    if is_schema_public():
        return

    report_file_path = os.path.join(settings.BACKUP_PATH, "entity_updated_at_" + tenant_schema()) + '.csv'

    if not os.path.isfile(report_file_path):
        logger.error("%s does not exist for tenant %s", report_file_path, tenant_schema())
        return 

    df = pd.read_csv(report_file_path, delimiter=';')
    df["updated_at"] = pd.to_datetime(df["updated_at"])

    from core.models import Entity
    total = 0
    queryset = Entity.objects.filter(updated_at__date=datetime.date(2022, 10, 27))
    for entity in queryset.iterator(chunk_size=10000):
        result = df[df["id"].str.match(str(entity.id))]
        if len(result.index) > 0:
            match = result.iloc[0]
            entity.updated_at = match["updated_at"]
            entity.save()
            total += 1

    logger.error("Updated updated_at for %i entities in schema %s ", total, tenant_schema())

import csv
import os

from django.conf import settings

from core.lib import tenant_schema, get_full_url
from deploy_task.utils import DeployCommandBase
from file.models import FileFolder


def write_missing_file_report():
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


class Command(DeployCommandBase):
    deploy_task = write_missing_file_report

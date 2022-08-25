import csv
import mimetypes
import os
import zipfile

import requests

from core.lib import get_tmp_file_path
from user.models import User


def build_avatar_export(user):
    zip_path = get_tmp_file_path(user, "avatar_export.zip")
    csv_path = get_tmp_file_path(user, "avatar_export.csv")

    try:
        zip_file = zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED)

        with open(csv_path, 'w') as fh:
            writer = csv.writer(fh, delimiter=';', quotechar='"')
            writer.writerow(['name', 'email', 'avatar'])
            for record in User.objects.filter(is_active=True):
                picture = None

                if record.picture:
                    try:
                        data, extension = _fetch_avatar(record.picture)
                        picture = f"{record.guid}{extension}"
                        zip_file.writestr(picture, data)
                    except Exception:
                        picture = None

                writer.writerow([record.name, record.email, picture])

        with open(csv_path, 'r') as fh:
            zip_file.writestr("summary.csv", fh.read())

        zip_file.close()

        with open(zip_path, 'rb') as fh:
            return fh.read()
    finally:
        os.unlink(csv_path)
        os.unlink(zip_path)


class CouldNotLoadPictureError(Exception):
    pass


def _fetch_avatar(url):
    response = requests.get(url)
    if not response.ok:
        raise CouldNotLoadPictureError()

    extension = mimetypes.guess_extension(response.headers['content-type'])

    return (response.content, extension)

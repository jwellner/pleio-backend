import csv
import mimetypes
import os
import zipfile

import requests

from concierge.api import fetch_avatar
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
                try:
                    data, extension = fetch_avatar_image(record)
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


def fetch_avatar_image(user: User):
    try:
        data = fetch_avatar(user) or {}
        url = data.get('originalAvatarUrl')

        assert url, "No url found"

        response = requests.get(url, timeout=3600)
        assert response.ok, response.reason

        return (response.content,
                mimetypes.guess_extension(response.headers['content-type']))
    except Exception:
        raise CouldNotLoadPictureError()


def compress_path(path):
    target_path = os.path.join(os.path.dirname(path), os.path.basename(path) + '.zip')

    zip_file = zipfile.ZipFile(target_path, mode='w', compression=zipfile.ZIP_DEFLATED)
    add_to_zip_recursive(path, '', zip_file)
    zip_file.close()

    return target_path


def add_to_zip_recursive(root, path, zip_file):
    try:
        for filename in os.listdir(os.path.join(root, path)):
            add_to_zip_recursive(root=root,
                                 path=os.path.join(path, filename),
                                 zip_file=zip_file)
    except NotADirectoryError:
        if path == '':
            zip_file.write(root, arcname=os.path.basename(root))
        else:
            zip_file.write(os.path.join(root, path), arcname=path)

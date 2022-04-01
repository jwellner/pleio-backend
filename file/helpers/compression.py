import mimetypes
import re
from os import path
from core.lib import get_mimetype
from file.models import FileFolder


def get_download_filename(f):
    filename = f.title

    mime_type = get_mimetype(f.upload.path)

    if mime_type:
        _, ext = path.splitext(f.title)

        # guess_all_extensions does no init? -> https://github.com/python/cpython/blob/3.8/Lib/mimetypes.py#L160
        mimetypes.init()
        # bug in guess_all_extensions where they convert all input to lowercase,
        # but the mimetype uses camelcase macroEnabled -> https://github.com/python/cpython/blob/3.8/Lib/mimetypes.py#L171
        mimetypes.add_type('application/vnd.ms-excel.sheet.macroenabled.12', '.xlsm')

        guess_all_extensions = mimetypes.guess_all_extensions(mime_type)

        # return title if has valid extension
        if ext in guess_all_extensions:
            pass

        # try add extension based on mimetype, else return title as name
        elif mimetypes.guess_extension(mime_type):
            filename = f.title + mimetypes.guess_extension(mime_type)

    filename = re.sub(r'[^a-zA-Z0-9\-\._]', '-', filename)

    return filename


def add_folders_to_zip(zip_file, folders, user, file_path):
    for folder in folders:
        files = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=False)
        file_path = path.join(file_path, folder.title)
        for f in files:
            zip_file.writestr(path.join(file_path, get_download_filename(f)), f.upload.read())
        sub_folders = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=True)
        add_folders_to_zip(zip_file, sub_folders, user, file_path)

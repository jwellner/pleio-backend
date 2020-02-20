import os
from file.models import FileFolder


def add_folders_to_zip(zip_file, folders, user, path):
    for folder in folders:
        files = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=False)
        path = os.path.join(path, folder.title)
        for f in files:
            zip_file.writestr(os.path.join(path, os.path.basename(f.upload.name)), f.upload.read())
        sub_folders = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=True)
        add_folders_to_zip(zip_file, sub_folders, user, path)

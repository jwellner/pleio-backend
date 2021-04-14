import mimetypes
from file.models import FileFolder
from os import path
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO


def get_download_filename(f):

    filename = f.title

    if f.mime_type:
        _, ext = path.splitext(f.title)
        guess_all_extensions = mimetypes.guess_all_extensions(f.mime_type)

        # if more exemptions, make function
        if ext == '.csv' and f.mime_type == 'text/plain':
            guess_all_extensions.append('.csv')

        # return title if has valid extension
        if ext in guess_all_extensions:
            pass

        # try add extension based on mimetype, else return title as name
        elif mimetypes.guess_extension(f.mime_type):
            filename = f.title + mimetypes.guess_extension(f.mime_type)

    return filename


def add_folders_to_zip(zip_file, folders, user, file_path):
    for folder in folders:
        files = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=False)
        file_path = path.join(file_path, folder.title)
        for f in files:
            zip_file.writestr(path.join(file_path, get_download_filename(f)), f.upload.read())
        sub_folders = FileFolder.objects.visible(user).filter(parent=folder.id, is_folder=True)
        add_folders_to_zip(zip_file, sub_folders, user, file_path)


def generate_thumbnail(file: FileFolder, size):

    thumbnail_size = (size, size)
    infile = file.upload.open()

    try:
        with Image.open(infile) as im:
            im.thumbnail(thumbnail_size, Image.LANCZOS)
            with BytesIO() as output:
                im = im.convert('RGB')
                im.save(output, "JPEG")
                contents = output.getvalue()
                file_name = str(file.id) + '.jpg'
                file.thumbnail.save(file_name, ContentFile(contents))

    except IOError:
        print("cannot create thumbnail for", infile)

def resize_and_update_image(file: FileFolder, max_width = 1400, max_height = 2000):
    """
    Resize FileFolder image to max bounderies
    """
    infile = file.upload.open()

    with Image.open(infile) as im:
        im.thumbnail((max_width, max_height), Image.LANCZOS)
        output = BytesIO()
        im = im.convert('RGB')
        im.save(output, 'JPEG')
        contents = output.getvalue()
        file_name = str(file.id) + '.jpg'
        file.upload.save(file_name, ContentFile(contents))

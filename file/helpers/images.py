from file.models import FileFolder
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO


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


def resize_and_update_image(file: FileFolder, max_width=1400, max_height=2000):
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


def resize_and_save_as_png(file: FileFolder, max_width=180, max_height=180):
    """
    Resize FileFolder image to png
    """
    infile = file.upload.open()

    with Image.open(infile) as im:
        im.thumbnail((max_width, max_height), Image.LANCZOS)
        output = BytesIO()
        im = im.convert('RGB')
        im.save(output, 'PNG')
        contents = output.getvalue()
        file_name = str(file.id) + '.png'
        file.upload.save(file_name, ContentFile(contents))

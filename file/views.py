import os
import tempfile
import zipfile
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from file.models import FileFolder
from file.helpers import add_folders_to_zip
from django.http import StreamingHttpResponse, FileResponse

def download(request, file_id=None, file_name=None):
    user = request.user

    if not file_id or not file_name:
        raise Http404("File not found")

    try:
        entity = FileFolder.objects.visible(user).get(id=file_id)
        response = StreamingHttpResponse(streaming_content=entity.upload.open(), content_type=entity.mime_type)
        response['Content-Length'] = entity.upload.size
        response['Content-Disposition'] = "attachment; filename=%s" % file_name
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")

    raise Http404("File not found")


def bulk_download(request):
    user = request.user

    file_ids = request.GET.getlist('file_guids[]')
    folder_ids = request.GET.getlist('folder_guids[]')

    if not file_ids and not folder_ids:
        raise Http404("File not found")

    _, temp_file_path = tempfile.mkstemp()

    zip_path = temp_file_path + '.zip'
    zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)

    # Add selected files to zip
    files = FileFolder.objects.visible(user).filter(id__in=file_ids, is_folder=False)
    for f in files:
        zipf.writestr(os.path.basename(f.upload.name), f.upload.read())

    # Add selected folders to zip
    folders = FileFolder.objects.visible(user).filter(id__in=folder_ids, is_folder=True)
    add_folders_to_zip(zipf, folders, user, '')

    zipf.close()

    response = FileResponse(open(zip_path, 'rb'))
    response['Content-Disposition'] = "attachment; filename=file_contents.zip"

    return response

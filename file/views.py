from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from file.models import FileFolder
from django.http import StreamingHttpResponse

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

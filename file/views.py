import zipfile
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, FileResponse, StreamingHttpResponse
from django.views.decorators.cache import cache_control
from django.shortcuts import redirect
from core.lib import get_tmp_file_path
from core.models import Entity
from core.constances import USER_ROLES
from file.models import FileFolder
from file.helpers import add_folders_to_zip, generate_thumbnail, get_download_filename
from os import path


def download(request, file_id=None, file_name=None):
    # pylint: disable=unused-argument
    user = request.user
    size = request.GET.get('size', None)

    if not file_id:
        raise Http404("File not found")

    try:
        entity = FileFolder.objects.visible(user).get(id=file_id)

        if entity.group and entity.group.is_closed and not entity.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            raise Http404("File not found")

        if entity.scan_incidents.count() > 0:
            raise Http404("File not found")

        return_file = entity

        if size:
            resized_image = entity.get_resized_image(size)

            if resized_image:
                return_file = resized_image
            else:
                return redirect(entity.download_url)

        attachment_or_inline = "attachment" if not return_file.mime_type else "inline"
        response = StreamingHttpResponse(streaming_content=return_file.upload.open(), content_type=return_file.mime_type)
        response['Content-Length'] = return_file.upload.size
        response['Content-Disposition'] = f"{attachment_or_inline}; filename=%s" % get_download_filename(entity)
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")

@cache_control(public=True, max_age=15724800)
def embed(request, file_id=None, file_name=None):
    # pylint: disable=unused-argument
    user = request.user
    size = request.GET.get('size', None)

    if not file_id:
        raise Http404("File not found")

    try:
        entity = FileFolder.objects.visible(user).get(id=file_id)

        if entity.group and entity.group.is_closed and not entity.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            raise Http404("File not found")

        if entity.scan_incidents.count() > 0:
            raise Http404("File not found")

        return_file = entity

        if size:
            resized_image = entity.get_resized_image(size)

            if resized_image:
                return_file = resized_image
            else:
                return redirect(entity.embed_url)

        response = StreamingHttpResponse(streaming_content=return_file.upload.open(), content_type=return_file.mime_type)
        response['Content-Length'] = return_file.upload.size
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")

@cache_control(public=True, max_age=15724800)
def featured(request, entity_guid=None):
    size = request.GET.get('size', None)
    if not entity_guid:
        raise Http404("File not found")

    try:
        # don't check user access on featured images because they are also used in email
        entity = Entity.objects.get_subclass(id=entity_guid)

        if hasattr(entity, 'featured_image') and entity.featured_image:
            if entity.featured_image.scan_incidents.count() > 0:
                raise Http404("File not found")

            return_file = entity.featured_image

            if size:
                resized_image = entity.featured_image.get_resized_image(size)

                if resized_image:
                    return_file = resized_image
                else:
                    return redirect(entity.featured_image_url)

            response = StreamingHttpResponse(streaming_content=return_file.upload.open(), content_type=return_file.mime_type)
            response['Content-Length'] = return_file.upload.size
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

    temp_file_path = get_tmp_file_path(user, ".zip")
    zipf = zipfile.ZipFile(temp_file_path, 'w', zipfile.ZIP_DEFLATED)

    # Add selected files to zip
    files = FileFolder.objects.visible(user).filter(id__in=file_ids, is_folder=False)
    for f in files:
        if f.group and f.group.is_closed and not f.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            continue
        if f.scan_incidents.count() > 0:
            continue
        zipf.writestr(path.basename(get_download_filename(f)), f.upload.read())

    # Add selected folders to zip
    folders = FileFolder.objects.visible(user).filter(id__in=folder_ids, is_folder=True)
    add_folders_to_zip(zipf, folders, user, '')

    zipf.close()

    response = FileResponse(open(temp_file_path, 'rb'))
    response['Content-Disposition'] = "attachment; filename=file_contents.zip"

    return response

@cache_control(public=True, max_age=15724800)
def thumbnail(request, file_id=None):
    user = request.user

    if not file_id:
        raise Http404("File not found")

    try:
        entity = FileFolder.objects.visible(user).get(id=file_id)

    except ObjectDoesNotExist:
        raise Http404("File not found")

    if entity.scan_incidents.count() > 0:
        raise Http404("File not found")

    if not entity.thumbnail:
        generate_thumbnail(entity, 153)

    if entity.thumbnail:
        response = FileResponse(entity.thumbnail.open())
        return response

    raise Http404("File not found")

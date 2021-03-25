import logging
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity, Group
from core.views import default, entity_view
from file.models import FileFolder
from elgg.models import FriendlyUrlMap, GuidMap

logger = logging.getLogger(__name__)

def redirect_view(request, entity_id):
    user = request.user

    entity = None

    if entity_id:
        try:
            mapper = GuidMap.objects.get(id=int(entity_id))

            if mapper.object_type == "group":
                entity = Group.objects.visible(user).get(id=mapper.guid)
            else:
                entity = Entity.objects.visible(user).select_subclasses().get(id=mapper.guid)

        except ObjectDoesNotExist:
            pass

    if entity and hasattr(entity, 'url'):
        return redirect(entity.url, permanent=True)

    return entity_view(request)

def redirect_download(request, file_id):
    user = request.user

    file = None

    if file_id:
        try:
            mapper = GuidMap.objects.filter(object_type='file').get(id=int(file_id))
            file = FileFolder.objects.visible(user).get(id=mapper.guid)

            return redirect(file.download_url, permanent=True)

        except ObjectDoesNotExist:
            pass

    return entity_view(request)

def redirect_friendly_url(request, friendly_url):
    user = request.user
    if friendly_url:
        try:
            object_id = FriendlyUrlMap.objects.get(url=friendly_url).object_id
            entity = Entity.objects.visible(user).get_subclass(id=object_id)

            return redirect(entity.url, permanent=True)
        except Exception:
            pass

    return default(request)
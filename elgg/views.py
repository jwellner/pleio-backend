from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity, Group
from core.views import entity_view
from elgg.models import GuidMap

def entity_redirect(request, entity_id):
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
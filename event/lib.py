from django.utils.text import slugify
from core.lib import get_base_url

def get_url(obj, context):
    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return get_base_url(context) + '{}/events/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()
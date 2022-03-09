from django.utils.text import slugify
from graphql import GraphQLError
from core.constances import INVALID_NAME
from core.lib import get_base_url

def get_url(obj, request):
    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return get_base_url() + '{}/events/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()


def validate_name(name):
    if not name or not len(name.strip()) > 2:
        raise GraphQLError(INVALID_NAME)
    return name.strip()

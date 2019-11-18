from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError
from core.models import User, Entity, Group
from file.models import FileFolder
from .query_viewer import resolve_viewer
from .query_site import resolve_site
from .query_entities import resolve_entities
from .query_groups import resolve_groups
from .query_bookmarks import resolve_bookmarks
from .query_search import resolve_search
from .query_users import resolve_users
from .query_trending import resolve_trending
from .query_notifications import resolve_notifications
from .query_recommended import resolve_recommended
from .query_top import resolve_top
from core.constances import COULD_NOT_FIND, ORDER_DIRECTION, ORDER_BY

query = ObjectType("Query")

query.set_field("viewer", resolve_viewer)
query.set_field("site", resolve_site)
query.set_field("entities", resolve_entities)
query.set_field("groups", resolve_groups)
query.set_field("bookmarks", resolve_bookmarks)
query.set_field("search", resolve_search)
query.set_field("users", resolve_users)
query.set_field("notifications", resolve_notifications)
query.set_field("trending", resolve_trending)
query.set_field("recommended", resolve_recommended)
query.set_field("top", resolve_top)


@query.field("entity")
def resolve_entity(
    _,
    info,
    guid=None,
    username=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context.user

    entity = None

    try:
        entity = Entity.objects.visible(user).get_subclass(id=guid)
    except ObjectDoesNotExist:
        pass

    # Also try to get User, Group, Comment, FileFolder
    # TODO: make frontend use separate queries for those types?
    if not entity:
        try:
            entity = Group.objects.visible(user).get(id=guid)
        except ObjectDoesNotExist:
            pass

    if not entity:
        try:
            entity = FileFolder.objects.visible(user).get(id=guid)
        except ObjectDoesNotExist:
            pass

    if not entity:
        try:
            if username:
                guid = username
            entity = User.objects.visible(user).get(id=guid)
        except ObjectDoesNotExist:
            pass

    if not entity:
        raise GraphQLError(COULD_NOT_FIND)

    return entity

# TODO: Implement breadcrumb

@query.field("breadcrumb")
def resolve_breadcrumb(_, info, guid=None):
    # pylint: disable=unused-argument
    return []


@query.field('filters')
def resolve_filters(_, info):
    # pylint: disable=unused-argument
    return {
        'users': None
    }

@query.field("files")
def resolve_files(_, info, containerGuid=None, filter=None, orderBy=ORDER_BY.timeCreated, orderDirection=ORDER_DIRECTION.asc, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    return {
        'total': 0,
        'canWrite': False,
        'edges': [],
    }


# TODO: Implement files

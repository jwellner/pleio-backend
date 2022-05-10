from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError
from core.models import Entity, Group, EntityView, EntityViewCount
from user.models import User
from .query_bookmarks import resolve_bookmarks
from .query_entities import resolve_entities
from .query_filters import resolve_filters
from .query_groups import resolve_groups
from .query_members import resolve_members
from .query_notifications import resolve_notifications
from .query_recommended import resolve_recommended
from .query_search import resolve_search
from .query_site import resolve_site, resolve_site_settings, resolve_site_stats
from .query_site_users import resolve_site_users
from .query_top import resolve_top
from .query_trending import resolve_trending
from .query_users import resolve_users
from .query_users_by_birth_date import resolve_users_by_birth_date
from .query_viewer import resolve_viewer
from core.constances import USER_NOT_MEMBER_OF_GROUP, USER_ROLES

query = ObjectType("Query")

query.set_field("bookmarks", resolve_bookmarks)
query.set_field("entities", resolve_entities)
query.set_field("filters", resolve_filters)
query.set_field("groups", resolve_groups)
query.set_field("members", resolve_members)
query.set_field("notifications", resolve_notifications)
query.set_field("recommended", resolve_recommended)
query.set_field("search", resolve_search)
query.set_field("site", resolve_site)
query.set_field("siteSettings", resolve_site_settings)
query.set_field("siteStats", resolve_site_stats)
query.set_field("siteUsers", resolve_site_users)
query.set_field("top", resolve_top)
query.set_field("trending", resolve_trending)
query.set_field("users", resolve_users)
query.set_field("usersByBirthDate", resolve_users_by_birth_date)
query.set_field("viewer", resolve_viewer)


@query.field("entity")
def resolve_entity(
    _,
    info,
    guid=None,
    username=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    entity = None

    try:
        entity = Entity.all_objects.visible(user).get_subclass(id=guid)

        if entity.group and entity.group.is_closed and not entity.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    except ObjectDoesNotExist:
        pass

    # Also try to get User, Group, Comment
    # TODO: make frontend use separate queries for those types?
    if not entity:
        try:
            entity = Group.objects.visible(user).get(id=guid)
        except ObjectDoesNotExist:
            pass

    if not entity:
        try:
            if username:
                guid = username
            entity = User.objects.visible(user).get(id=guid)
        except ObjectDoesNotExist:
            pass

    # check if draft exists
    if not entity:
        if user.is_authenticated:
            try:
                entity = Entity.all_objects.draft(user).get_subclass(id=guid)
            except ObjectDoesNotExist:
                pass

    if not entity:
        return None

    # Increase view count of entities
    try:
        Entity.all_objects.get(id=entity.id)
        try:
            view_count = EntityViewCount.objects.get(entity=entity)
        except ObjectDoesNotExist:
            view_count = None

        if view_count:
            view_count.views += 1
            view_count.save(update_fields=["views"])
        else:
            EntityViewCount.objects.create(entity=entity, views=1)

        if user.is_authenticated:
            EntityView.objects.create(entity=entity, viewer=user)
    except ObjectDoesNotExist:
        pass

    return entity

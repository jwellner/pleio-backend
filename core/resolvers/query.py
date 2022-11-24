from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import F
from django.utils import timezone
from graphql import GraphQLError

from core.constances import USER_NOT_MEMBER_OF_GROUP, USER_ROLES
from core.models import Entity, EntityView, EntityViewCount, Group
from user.models import User
from .query_meetings import resolve_query_appointment_data, resolve_query_appointment_times
from .query_bookmarks import resolve_bookmarks
from .query_entities import resolve_entities
from .query_filters import resolve_filters
from .query_groups import resolve_groups
from .query_members import resolve_members
from .query_notifications import resolve_notifications
from .query_recommended import resolve_recommended
from .query_revisions import resolve_revisions
from .query_search import resolve_search, resolve_search_journal
from .query_site import resolve_site, resolve_site_settings, resolve_site_stats
from .query_site_agreements import (resolve_site_agreements,
                                    resolve_site_custom_agreements)
from .query_site_users import resolve_site_users
from .query_tags import resolve_list_tags
from .query_top import resolve_top
from .query_trending import resolve_trending
from .query_users import resolve_users
from .query_users_by_birth_date import resolve_users_by_birth_date
from .query_viewer import resolve_viewer

query = ObjectType("Query")

query.set_field("bookmarks", resolve_bookmarks)
query.set_field("entities", resolve_entities)
query.set_field("filters", resolve_filters)
query.set_field("groups", resolve_groups)
query.set_field("members", resolve_members)
query.set_field("notifications", resolve_notifications)
query.set_field("recommended", resolve_recommended)
query.set_field("search", resolve_search)
query.set_field("searchJournal", resolve_search_journal)
query.set_field("site", resolve_site)
query.set_field("siteAgreements", resolve_site_agreements)
query.set_field("siteCustomAgreements", resolve_site_custom_agreements)
query.set_field("siteSettings", resolve_site_settings)
query.set_field("siteStats", resolve_site_stats)
query.set_field("siteUsers", resolve_site_users)
query.set_field("top", resolve_top)
query.set_field("trending", resolve_trending)
query.set_field("users", resolve_users)
query.set_field("usersByBirthDate", resolve_users_by_birth_date)
query.set_field("trending", resolve_trending)
query.set_field("recommended", resolve_recommended)
query.set_field("top", resolve_top)
query.set_field("filters", resolve_filters)
query.set_field("tags", resolve_list_tags)
query.set_field("viewer", resolve_viewer)
query.set_field("revisions", resolve_revisions)
query.set_field("appointmentData", resolve_query_appointment_data)
query.set_field("appointmentTimes", resolve_query_appointment_times)


@query.field("entity")
def resolve_entity(
        _,
        info,
        guid=None,
        username=None,
        incrementViewCount=False
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    entity = None

    try:
        entity = Entity.objects.visible(user).get_subclass(id=guid)
        if entity.group and entity.group.is_closed and not entity.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)
    except (ObjectDoesNotExist, ValidationError):
        pass

    # Also try to get User, Group, Comment
    # TODO: make frontend use separate queries for those types?
    if not entity:
        try:
            entity = Group.objects.visible(user).get(id=guid)
        except (ObjectDoesNotExist, ValidationError):
            pass

    if not entity:
        try:
            if username:
                guid = username
            entity = User.objects.visible(user).get(id=guid)
        except (ObjectDoesNotExist, ValidationError):
            pass

    # check if draft exists
    if not entity:
        if user.is_authenticated:
            try:
                entity = Entity.objects.draft(user).get_subclass(id=guid)
            except (ObjectDoesNotExist, ValidationError):
                pass

    if not entity:
        try:
            entity = Entity.objects.archived(user).get_subclass(id=guid)
        except (ObjectDoesNotExist, ValidationError):
            pass

    if not entity:
        return None

    if incrementViewCount:
        increment_view_count(entity, info.context["request"])

    return entity


def increment_view_count(entity, request):
    # Increase view count of entities
    user = request.user

    if user.is_authenticated:
        EntityView.objects.create(entity=entity, viewer=user)
        views = EntityView.objects.filter(entity=entity, viewer=user).count()
    else:
        sessionid = request.COOKIES.get('sessionid', None)
        EntityView.objects.create(entity=entity, session=sessionid)
        views = EntityView.objects.filter(entity=entity, session=sessionid).count()

    if views == 1:
        if EntityViewCount.objects.filter(entity_id=entity.guid).exists():
            EntityViewCount.objects.filter(entity_id=entity.guid).update(views=F('views') + 1, updated_at=timezone.now())
        else:
            EntityViewCount.objects.create(entity_id=entity.guid, views=1)

    entity.save()

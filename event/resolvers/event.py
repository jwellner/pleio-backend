from ariadne import ObjectType
from core.resolvers import shared
from django.db.models import Q
from core.lib import datetime_isoformat


def conditional_state_filter(state):
    if state:
        return Q(state=state)

    return Q()


event = ObjectType("Event")

@event.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return "event"

@event.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None

@event.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group

@event.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured

@event.field("isHighlighted")
def resolve_is_highlighted(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@event.field("isRecommended")
def resolve_is_recommended(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@event.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@event.field("startDate")
def resolve_start_date(obj, info):
    # pylint: disable=unused-argument
    return datetime_isoformat(obj.start_date)

@event.field("endDate")
def resolve_end_date(obj, info):
    # pylint: disable=unused-argument
    return datetime_isoformat(obj.end_date)

@event.field("source")
def resolve_source(obj, info):
    # pylint: disable=unused-argument
    return obj.external_link

@event.field("attendEventWithoutAccount")
def resolve_attend_event_without_account(obj, info):
    # pylint: disable=unused-argument
    return obj.attend_event_without_account

@event.field("maxAttendees")
def resolve_max_attendees(obj, info):
    # pylint: disable=unused-argument
    if obj.max_attendees:
        return str(obj.max_attendees)
    return None

@event.field("isAttending")
def resolve_is_attending(obj, info):
    # pylint: disable=unused-argument
    attendee = obj.get_attendee(info.context["request"].user)

    if attendee:
        return attendee.state

    return None

@event.field("attendees")
def resolve_attendees(obj, info, limit=20, offset=0, state=None):
    # pylint: disable=unused-argument

    user = info.context["request"].user
    if not user.is_authenticated:
        return {
            "total": 0,
            "totalMaybe": 0,
            "totalReject": 0,
            "edges": []
        }

    # only return attending registered users
    # TODO: create other type for edges to support external attendees?
    qs = obj.attendees.exclude(user__isnull=True)
    qs = qs.filter(conditional_state_filter(state))
    qs = qs[offset:offset+limit]

    users = [item.user for item in qs]

    return {
        "total": obj.attendees.filter(state="accept").count(),
        "totalMaybe": obj.attendees.filter(state="maybe").count(),
        "totalReject": obj.attendees.filter(state="reject").count(),
        "edges": users
    }

@event.field("attendeesWithoutAccount")
def resolve_attendees_without_account(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user
    if not user.is_authenticated:
        return 0

    return obj.attendees.exclude(user__isnull=False).count()


event.set_field("guid", shared.resolve_entity_guid)
event.set_field("status", shared.resolve_entity_status)
event.set_field("title", shared.resolve_entity_title)
event.set_field("description", shared.resolve_entity_description)
event.set_field("richDescription", shared.resolve_entity_rich_description)
event.set_field("excerpt", shared.resolve_entity_excerpt)
event.set_field("tags", shared.resolve_entity_tags)
event.set_field("timeCreated", shared.resolve_entity_time_created)
event.set_field("timeUpdated", shared.resolve_entity_time_updated)
event.set_field("timePublished", shared.resolve_entity_time_published)
event.set_field("statusPublished", shared.resolve_entity_status_published)
event.set_field("canEdit", shared.resolve_entity_can_edit)
event.set_field("canComment", shared.resolve_entity_can_comment)
event.set_field("canBookmark", shared.resolve_entity_can_bookmark)
event.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
event.set_field("accessId", shared.resolve_entity_access_id)
event.set_field("writeAccessId", shared.resolve_entity_write_access_id)
event.set_field("featured", shared.resolve_entity_featured)
event.set_field("canComment", shared.resolve_entity_can_comment)
event.set_field("comments", shared.resolve_entity_comments)
event.set_field("commentCount", shared.resolve_entity_comment_count)
event.set_field("views", shared.resolve_entity_views)
event.set_field("owner", shared.resolve_entity_owner)
event.set_field("isPinned", shared.resolve_entity_is_pinned)

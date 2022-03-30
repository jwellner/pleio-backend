from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from core.resolvers import shared
from django.db.models import Q, Case, When
from core.constances import ENTITY_STATUS
from core.lib import datetime_isoformat
from event.models import Event, EventAttendee
from core.constances import ATTENDEE_ORDER_BY, ORDER_DIRECTION

def conditional_state_filter(state):
    if state:
        return Q(state=state)

    return Q()


event = ObjectType("Event")

@event.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return "event"

@event.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()

@event.field("children")
def resolve_children(obj, info):
    # pylint: disable=unused-argument
    """
    Children fields published and isArchived are kept in sync with the parent event, see signals in event/models.py
    """
    if obj.status_published == ENTITY_STATUS.PUBLISHED:
        return obj.children.visible(info.context["request"].user)
    return Event.all_objects.filter(parent=obj)

@event.field("parent")
def resolve_parent(obj, info):
    # pylint: disable=unused-argument
    return obj.parent

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
    user = info.context["request"].user

    if user.is_authenticated:
        attendee = obj.get_attendee(user, user.email)
        if attendee:
            return attendee.state

    return None

@event.field("isAttendingParent")
def resolve_is_attending_parent(obj, info):
    # pylint: disable=unused-argument
    if obj.parent is None:
        return True
    try:
        EventAttendee.objects.get(user=info.context["request"].user, event=obj.parent, state='accept')
        return True
    except ObjectDoesNotExist:
        pass
    return False

@event.field("attendees")
def resolve_attendees(obj, info, query=None, limit=20, offset=0, state=None,
                      orderBy=ATTENDEE_ORDER_BY.name, orderDirection=ORDER_DIRECTION.asc, isCheckedIn=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments


    user = info.context["request"].user

    if not user.is_authenticated:
        return {
            "total": obj.attendees.filter(state="accept").count(),
            "totalMaybe": 0,
            "totalReject": 0,
            "totalWaitinglist": 0,
            "edges": []
        }

    can_write = obj.can_write(user)
    qs = obj.attendees.all()

    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(id__iexact=query)
        )

    qs = qs.filter(conditional_state_filter(state))

    if isCheckedIn is False:
        qs = qs.filter(checked_in_at__isnull = True)
    elif isCheckedIn is True:
        qs = qs.filter(checked_in_at__isnull = False)

    if orderBy == ATTENDEE_ORDER_BY.email: 
        order_by = 'email'
    elif orderBy == ATTENDEE_ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ATTENDEE_ORDER_BY.timeCheckedIn:
        order_by = 'checked_in_at'
    elif orderBy == ATTENDEE_ORDER_BY.name:
        qs = qs.annotate(
            names=Case(
                When(user=None, then='name'),
                default='user__name',
        ))
        order_by = 'names'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    qs = qs.order_by(order_by)
    qs = qs[offset:offset+limit]

    # email adresses only for user with event write permissions
    def get_email(item, can_write):
        if can_write:
            return item.user.email if item.user else item.email
        return ""

    attendees = [
        {
        "email": get_email(item, can_write),
        "name": item.user.name if item.user else item.name, 
        "state": item.state,
        "icon": item.user.icon if item.user else None, 
        "url": item.user.url if item.user else None,
        "timeCheckedIn": item.checked_in_at
        } 
        for item in qs]

    return {
        "total": obj.attendees.filter(state="accept").count(),
        "totalMaybe": obj.attendees.filter(state="maybe").count(),
        "totalReject": obj.attendees.filter(state="reject").count(),
        "totalWaitinglist": obj.attendees.filter(state="waitinglist").count(),
        "edges": attendees
    }


event.set_field("guid", shared.resolve_entity_guid)
event.set_field("status", shared.resolve_entity_status)
event.set_field("title", shared.resolve_entity_title)
event.set_field("abstract", shared.resolve_entity_abstract)
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

from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from core.resolvers import shared
from django.db.models import Q, Case, When
from core.constances import ENTITY_STATUS
from core.lib import datetime_isoformat
from event.models import Event, EventAttendee
from event.resolvers import shared as event_shared
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
        qs = obj.children.visible(info.context["request"].user)
    else:
        qs = Event.objects.filter(parent=obj)
    return qs.order_by('start_date', 'created_at')


@event.field("parent")
def resolve_parent(obj, info):
    # pylint: disable=unused-argument
    return obj.parent


@event.field('slotsAvailable')
def resolve_slots_available(obj: Event, info):
    # pylint: disable=unused-argument
    return obj.slots_available


@event.field('slots')
def resolve_slots(obj: Event, info):
    # pylint: disable=unused-argument
    return [slot['name'] for slot in obj.get_slots()]


@event.field('alreadySignedUpInSlot')
def resolve_slot_already_signed_in_for_slot(obj, info):
    if not obj.parent:
        return None

    attending_events = event_shared.attending_events(info)
    return bool([n for n in obj.shared_via_slot if n in attending_events])


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


@event.field("location")
def resolve_location(obj, info):
    # pylint: disable=unused-argument
    return obj.location


@event.field("locationLink")
def resolve_location_link(obj, info):
    # pylint: disable=unused-argument
    return obj.location_link


@event.field("locationAddress")
def resolve_location_address(obj, info):
    # pylint: disable=unused-argument
    return obj.location_address


@event.field("ticketLink")
def resolve_ticket_link(obj, info):
    # pylint: disable=unused-argument
    return obj.ticket_link


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
        attendee = obj.get_attendee(user.email)
        if attendee:
            return attendee.state

    return None


@event.field("isAttendingParent")
def resolve_is_attending_parent(obj, info):
    # pylint: disable=unused-argument
    if obj.parent is None:
        return True

    user = info.context["request"].user

    if not user.is_authenticated:
        return False

    try:
        EventAttendee.objects.get(user=user, event=obj.parent, state='accept')
        return True
    except ObjectDoesNotExist:
        pass
    return False


@event.field("qrAccess")
def resolve_qr_access(obj, info):
    # pylint: disable=unused-argument
    return obj.qr_access


@event.field("attendees")
def resolve_attendees(obj, info, query=None, limit=20, offset=0, state=None,
                      orderBy=ATTENDEE_ORDER_BY.name, orderDirection=ORDER_DIRECTION.asc, isCheckedIn=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    user = info.context["request"].user

    if not user.is_authenticated:
        return {
            "total": obj.attendees.count(),
            "totalAccept": obj.attendees.filter(state="accept").count(),
            "totalWaitinglist": obj.attendees.filter(state="waitinglist").count(),
            "edges": [],
        }

    qs = obj.attendees.all()

    qs = qs.annotate(
        names=Case(
            When(user=None, then='name'),
            default='user__name',
        ))
    qs = qs.annotate(
        emails=Case(
            When(user=None, then='email'),
            default='user__email',
        ))

    if query:
        qs = qs.filter(
            Q(names__icontains=query) |
            Q(emails__icontains=query) |
            Q(id__iexact=query)
        )

    qs = qs.filter(conditional_state_filter(state))

    if isCheckedIn is False:
        qs = qs.filter(checked_in_at__isnull=True)
    elif isCheckedIn is True:
        qs = qs.filter(checked_in_at__isnull=False)

    if orderBy == ATTENDEE_ORDER_BY.email:
        order_by = 'email'
    elif orderBy == ATTENDEE_ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ATTENDEE_ORDER_BY.timeCheckedIn:
        order_by = 'checked_in_at'
    elif orderBy == ATTENDEE_ORDER_BY.name:
        order_by = 'names'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    qs = qs.order_by(order_by)
    qs = qs[offset:offset + limit]

    attendees = [item.as_attendee(user) for item in qs]

    notCheckedIn = obj.attendees.filter(checked_in_at__isnull=True)

    return {
        "total": len(attendees),
        "edges": attendees,
        "totalAccept": obj.attendees.filter(state="accept").count(),
        "totalAcceptNotCheckedIn": notCheckedIn.filter(state="accept").count(),
        "totalWaitinglist": obj.attendees.filter(state="waitinglist").count(),
        "totalWaitinglistNotCheckedIn": notCheckedIn.filter(state="waitinglist").count(),
        "totalMaybe": obj.attendees.filter(state="maybe").count(),
        "totalReject": obj.attendees.filter(state="reject").count(),
        "totalCheckedIn": obj.attendees.filter(checked_in_at__isnull=False).count(),
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
event.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
event.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
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

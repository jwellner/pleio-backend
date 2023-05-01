from django.utils import timezone
from graphql import GraphQLError

from core import constances
from core.constances import INVALID_DATE, COULD_NOT_ADD, NON_SUBEVENT_OPERATION
from core.lib import early_this_morning
from core.utils.convert import tiptap_to_text
from event.mail_builders.delete_event_attendees import submit_delete_event_attendees_mail
from event.models import EventAttendee, Event
from event.range.sync import EventRangeSync


def resolve_update_startenddate(entity, clean_input):
    if 'startDate' in clean_input:
        entity.start_date = clean_input.get("startDate")
    if 'endDate' in clean_input:
        entity.end_date = clean_input.get("endDate")
    if not entity.end_date:
        entity.end_date = entity.start_date

    if not entity.start_date or not entity.end_date:
        raise GraphQLError(INVALID_DATE)
    if entity.start_date > entity.end_date:
        raise GraphQLError(INVALID_DATE)


def resolve_update_location(entity, clean_input):
    if 'location' in clean_input:
        entity.location = clean_input.get("location")
    if 'locationLink' in clean_input:
        entity.location_link = clean_input.get("locationLink")
    if 'locationAddress' in clean_input:
        entity.location_address = clean_input.get("locationAddress")


def resolve_update_source(entity, clean_input):
    if 'source' in clean_input:
        entity.external_link = clean_input.get("source")


def resolve_update_ticket_link(entity, clean_input):
    if 'ticketLink' in clean_input:
        entity.ticket_link = clean_input['ticketLink']


def resolve_update_max_attendees(entity, clean_input):
    if 'maxAttendees' in clean_input:
        if clean_input.get("maxAttendees") == "":
            entity.max_attendees = None
        else:
            entity.max_attendees = int(clean_input.get("maxAttendees"))
        entity.process_waitinglist()


def resolve_update_rsvp(entity, clean_input):
    if 'rsvp' in clean_input:
        entity.rsvp = clean_input.get("rsvp")


def resolve_update_attend_without_account(entity, clean_input):
    if 'attendEventWithoutAccount' in clean_input:
        entity.attend_event_without_account = clean_input.get("attendEventWithoutAccount")


def resolve_update_enable_maybe_attend_event(entity, clean_input):
    if 'enableMaybeAttendEvent' in clean_input:
        entity.enable_maybe_attend_event = clean_input.get("enableMaybeAttendEvent")


def resolve_update_qr_access(entity, clean_input):
    if 'qrAccess' in clean_input:
        entity.qr_access = clean_input.get("qrAccess")


def resolve_update_slots_available(entity, clean_input):
    if 'slotsAvailable' in clean_input:
        # not allowed for sub-events
        if entity.parent:
            raise GraphQLError(NON_SUBEVENT_OPERATION)

        if not entity.id:
            raise GraphQLError(COULD_NOT_ADD)

        entity.slots_available = clean_input['slotsAvailable']


def resolve_delete_attendee(attendee):
    event = attendee.event

    if attendee.event.has_children():
        for child in event.children.all():
            child.delete_attendee(attendee.email)

    mail_info = attendee.as_mailinfo()
    mail_user = attendee.user

    attendee.delete()

    submit_delete_event_attendees_mail(event=event,
                                       mail_info=mail_info,
                                       user=mail_user)


def resolve_update_attendee_welcome_mail(entity, clean_input):
    if 'attendeeWelcomeMailSubject' in clean_input:
        entity.attendee_welcome_mail_subject = clean_input.get("attendeeWelcomeMailSubject")
    if 'attendeeWelcomeMailContent' in clean_input:
        entity.attendee_welcome_mail_content = clean_input.get("attendeeWelcomeMailContent")

    subject = (entity.attendee_welcome_mail_subject or '').strip()
    content = tiptap_to_text(entity.attendee_welcome_mail_content or '').strip()
    if content and not subject:
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendeeWelcomeMailSubject')
    if subject and not content:
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendeeWelcomeMailContent')


def attending_events(info):
    user = info.context["request"].user
    if user.is_authenticated:
        return [str(pk) for pk in EventAttendee.objects.filter(user=user, state="accept").values_list('event__id', flat=True)]
    # TODO: read from stored email in session?
    return []


def _maybe_isodatetime(timestamp):
    if isinstance(timestamp, timezone.datetime):
        return timestamp.isoformat()
    return timestamp


def resolve_update_range_settings(entity, clean_input):
    if 'rangeSettings' in clean_input:
        if entity.start_date < early_this_morning():
            raise GraphQLError(constances.EVENT_RANGE_IMMUTABLE)
        if entity.parent or (entity.pk and entity.children.count()):
            raise GraphQLError(constances.EVENT_RANGE_NOT_POSSIBLE)

        # update range_settings.
        entity.range_settings = clean_input['rangeSettings']
        entity.range_settings['repeatUntil'] = _maybe_isodatetime(entity.range_settings.get('repeatUntil'))
    elif entity.is_recurring:
        entity.range_settings['updateRange'] = not entity.range_ignore
    else:
        return

    if entity.range_settings['updateRange'] or not entity.range_starttime:
        entity.range_starttime = entity.start_date


def followup_range_setting_changes(entity):
    if entity.is_recurring:
        sync = EventRangeSync(entity)
        sync.followup_settings_change()


def assert_valid_new_range(clean_input):
    if 'rangeSettings' not in clean_input:
        return

    if not clean_input['rangeSettings'].get('repeatUntil'):
        return

    settings = clean_input['rangeSettings']
    start_date = clean_input['startDate']

    if settings['repeatUntil'] >= start_date:
        return

    raise GraphQLError(constances.EVENT_INVALID_REPEAT_UNTIL_DATE)


def assert_valid_updated_range(entity, clean_input):
    if 'rangeSettings' not in clean_input:
        return

    settings = clean_input['rangeSettings']
    if settings.get('repeatUntil'):
        start_date = clean_input.get('startDate') or entity.start_date
        if start_date <= settings.get('repeatUntil'):
            return
        raise GraphQLError(constances.EVENT_INVALID_REPEAT_UNTIL_DATE)

    if settings.get('instanceLimit'):
        if settings.get('instanceLimit') > Event.objects.get_range_before(entity).count():
            return
        raise GraphQLError(constances.EVENT_INVALID_REPEAT_INSTANCE_LIMIT)

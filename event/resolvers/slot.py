from ariadne import ObjectType

from event.models import EventAttendee

slot = ObjectType("EventSlot")


@slot.field('alreadySignedUpInSlot')
def resolve_slot_already_signed_in_for_slot(obj, info):
    user = info.context["request"].user
    if user.is_authenticated:
        attending_events = [str(pk) for pk in EventAttendee.objects.filter(user=user).values_list('event__id', flat=True)]
    else:
        # TODO: read from stored email in session?
        attending_events = []

    if not attending_events:
        return False

    return bool([n for n in obj['subEventGuids'] if n in attending_events])

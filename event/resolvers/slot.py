from ariadne import ObjectType

from event.resolvers import shared as event_shared

slot = ObjectType("EventSlot")


@slot.field('alreadySignedUpInSlot')
def resolve_slot_already_signed_in_for_slot(obj, info):
    attending_events = event_shared.attending_events(info)

    if not attending_events:
        return False

    return bool([n for n in obj['subEventGuids'] if n in attending_events])

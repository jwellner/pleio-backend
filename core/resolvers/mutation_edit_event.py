import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateparse
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_DATE
from core.resolvers.shared import access_id_to_acl
from core.models import FileFolder
from event.models import Event

def resolve_edit_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:  
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():

        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description", "")
        entity.rich_description = clean_input.get("richDescription")
        
        entity.tags = clean_input.get("tags", [])
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId", 0))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId", 0))

        if clean_input.get("featured"):
            entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
            entity.featured_video = clean_input.get("featured").get("video", None)
            if entity.featured_video:
                entity.featured_image = None
            elif clean_input.get("featured").get("image"):

                imageFile = FileFolder.objects.create(
                    owner=entity.owner, 
                    upload=clean_input.get("featured").get("image"), 
                    read_access=entity.read_access,
                    write_access=entity.write_access
                )

                entity.featured_image = imageFile

            entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        else:
            entity.featured_image = None
            entity.featured_position_y = 0
            entity.featured_video = None

        entity.is_featured = clean_input.get("isFeatured", False)

        if not clean_input.get("startDate", None) or not clean_input.get("endDate", None):
            raise GraphQLError(INVALID_DATE)

        entity.start_date = dateparse.parse_datetime(clean_input.get("startDate"))
        entity.end_date = dateparse.parse_datetime(clean_input.get("endDate"))

        if entity.start_date > entity.end_date:
            raise GraphQLError(INVALID_DATE)

        entity.external_link = clean_input.get("source", "")
        entity.location = clean_input.get("location", "")
        
        if clean_input.get("maxAttendees", None):
            entity.max_attendees = int(clean_input.get("maxAttendees"))

        entity.rsvp = clean_input.get("rsvp", False)
        entity.attend_event_without_account = clean_input.get("attendEventWithoutAccount", False)

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }

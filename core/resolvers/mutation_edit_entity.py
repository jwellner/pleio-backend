import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id, remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_SUBTYPE
from core.resolvers.shared import get_model_by_subtype, access_id_to_acl
from core.models import FileFolder

def resolve_edit_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    subtype = get_type(clean_input.get("guid"))
    entity_id = get_id(clean_input.get("guid"))

    model = get_model_by_subtype(subtype)

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        entity = model.objects.get(id=entity_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():

        entity.tags = clean_input.get("tags", [])

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

        if subtype in ["blog", "news"]:
            entity.title = clean_input.get("title")
            entity.description = clean_input.get("description", "")
            entity.rich_description = clean_input.get("richDescription")

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

        if subtype in ["blog"]:
            # TODO: subeditor may also set recommended
            if user.is_admin:
                entity.is_recommended = clean_input.get("isRecommended")

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }

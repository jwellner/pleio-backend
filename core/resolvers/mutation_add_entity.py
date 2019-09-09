import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE, ACCESS_TYPE
from core.resolvers.shared import get_model_by_subtype, access_id_to_acl
from core.models import Group, FileFolder
from core.resolvers.mutation_add_comment import resolve_add_comment


def resolve_add_entity(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if clean_input.get("subtype") == "comment":
        return resolve_add_comment(_, info, input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    model = get_model_by_subtype(clean_input.get("subtype"))

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    group = None

    if clean_input.get("containerGuid"):
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

        if not group.is_full_member(user) and not user.is_admin:
            raise GraphQLError("NOT_GROUP_MEMBER")

    with reversion.create_revision():
        # default fields for all entities
        entity = model()

        entity.owner = user
        entity.tags = clean_input.get("tags")

        if group:
            entity.group = group

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
        entity.write_access = [ACCESS_TYPE.user.format(user.id)]

        if clean_input.get("subtype") in ["blog", "news"]:
            entity.title = clean_input.get("title")
            entity.description = clean_input.get("description")
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

        if clean_input.get("subtype") in ["blog"]:
            # TODO: subeditor may also set recommended
            if user.is_admin:
                entity.is_recommended = clean_input.get("isRecommended")


        entity.save()

        reversion.set_user(user)
        reversion.set_comment("addEntity mutation")

    return {
        "entity": entity
    }

from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input, access_id_to_acl, tenant_schema
from core.models import Comment, Group
from core.resolvers.shared import clean_abstract
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, COULD_NOT_FIND_GROUP, \
    USER_NOT_MEMBER_OF_GROUP, USER_ROLES
from core.utils.convert import tiptap_to_text
from file.models import FileFolder
from file.tasks import resize_featured
from question.models import Question
from user.models import User

def resolve_toggle_best_answer(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        comment = Comment.objects.get(id=clean_input.get("guid"))
        question = Question.objects.visible(user).get(id=comment.object_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not question.can_choose_best_answer(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if question.best_answer == comment:
        question.best_answer = None
    else:
        question.best_answer = comment
    question.save()

    return {
        "entity": question
    }

def resolve_toggle_item_closed(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        question = Question.objects.visible(user).get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not question.can_close(user):
        raise GraphQLError(COULD_NOT_SAVE)

    question.is_closed = not question.is_closed
    question.save()

    return {
        "entity": question
    }

def resolve_add_question(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    entity = Question()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")
    entity.rich_description = clean_input.get("richDescription")
    entity.description = tiptap_to_text(entity.rich_description)
    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", None)
        entity.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        entity.featured_alt = clean_input.get("featured").get("alt", "")
        if entity.featured_video:
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):

            imageFile = FileFolder.objects.create(
                owner=entity.owner,
                upload=clean_input.get("featured").get("image"),
                read_access=entity.read_access,
                write_access=entity.write_access
            )

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None
        entity.featured_video_title = ""
        entity.featured_alt = ""

    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished")

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }

def resolve_edit_question(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Question.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if 'title' in clean_input:
        entity.title = clean_input.get("title")

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")
        entity.description = tiptap_to_text(entity.rich_description)

    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", "")
        entity.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        entity.featured_alt = clean_input.get("featured").get("alt", "")
        if entity.featured_video:
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):

            if entity.featured_image:
                imageFile = entity.featured_image
                imageFile.resized_images.all().delete()
            else:
                imageFile = FileFolder()

            imageFile.owner = entity.owner
            imageFile.read_access = entity.read_access
            imageFile.write_access = entity.write_access
            imageFile.upload = clean_input.get("featured").get("image")
            imageFile.save()

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None
        entity.featured_video_title = ""
        entity.featured_alt = ""

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished")

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        if 'groupGuid' in input:
            if input.get("groupGuid") is None:
                entity.group = None
            else:
                try:
                    group = Group.objects.get(id=clean_input.get("groupGuid"))
                    entity.group = group
                except ObjectDoesNotExist:
                    raise GraphQLError(COULD_NOT_FIND)

        if 'ownerGuid' in clean_input:
            try:
                owner = User.objects.get(id=clean_input.get("ownerGuid"))
                entity.owner = owner
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)

        if 'timeCreated' in clean_input:
            entity.created_at = clean_input.get("timeCreated")

    entity.save()

    return {
        "entity": entity
    }

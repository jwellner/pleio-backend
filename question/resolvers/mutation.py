from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.models import Comment, Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, COULD_NOT_FIND_GROUP, USER_NOT_MEMBER_OF_GROUP
from question.models import Question

def resolve_toggle_best_answer(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

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

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        question = Question.objects.visible(user).get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not question.can_write(user):
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
    # TODO: check if non admins can add news (roles)

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if group and not group.is_full_member(user) and not user.is_admin:
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    entity = Question()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")
    entity.description = clean_input.get("description")
    entity.rich_description = clean_input.get("richDescription")

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }

def resolve_edit_question(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
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
    if 'description' in clean_input:
        entity.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")

    entity.save()

    return {
        "entity": entity
    }

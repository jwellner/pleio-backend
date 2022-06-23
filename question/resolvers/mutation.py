from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input
from core.models import Comment
from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from question.models import Question


def resolve_toggle_best_answer(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

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

    shared.assert_authenticated(user)

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

    shared.assert_authenticated(user)

    group = shared.get_group(clean_input)

    shared.assert_group_member(user, group)

    entity = Question()

    entity.owner = user
    entity.group = group

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

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
    entity = load_entity_by_id(input['guid'], [Question])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)
        shared.resolve_update_owner(entity, clean_input)
        shared.resolve_update_time_created(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }

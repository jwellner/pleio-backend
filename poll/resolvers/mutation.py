from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateparse
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, ALREADY_VOTED, INVALID_ANSWER, INVALID_DATE
from core.lib import remove_none_from_dict, access_id_to_acl
from ..models import Poll, PollChoice

def resolve_add_poll(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = Poll()

    entity.owner = user

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")

    if 'timePublished' in clean_input:
        if clean_input.get("timePublished") is None:
            entity.published = None
        else:
            try:
                entity.published = dateparse.parse_datetime(clean_input.get("timePublished"))
            except ObjectDoesNotExist:
                raise GraphQLError(INVALID_DATE)

    entity.save()

    for choice in clean_input.get("choices"):
        PollChoice.objects.create(poll=entity, text=choice)

    return {
        "entity": entity
    }


def resolve_edit_poll(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Poll.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'title' in clean_input:
        entity.title = clean_input.get("title")

    if 'timePublished' in clean_input:
        if clean_input.get("timePublished") is None:
            entity.published = None
        else:
            try:
                entity.published = dateparse.parse_datetime(clean_input.get("timePublished"))
            except ObjectDoesNotExist:
                raise GraphQLError(INVALID_DATE)

    entity.save()

    entity.choices.all().delete()
    for choice in clean_input.get("choices"):
        PollChoice.objects.create(poll=entity, text=choice)

    return {
        "entity": entity
    }


def resolve_vote_on_poll(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        poll = Poll.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        poll_choice = PollChoice.objects.get(poll=poll, text=clean_input.get("response"))
    except ObjectDoesNotExist:
        raise GraphQLError(INVALID_ANSWER)

    for choice in poll.choices.all():
        if choice.has_voted(user):
            raise GraphQLError(ALREADY_VOTED)

    poll_choice.add_vote(user, 1)

    return {
        "entity": poll
    }

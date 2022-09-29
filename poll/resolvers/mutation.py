from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import ALREADY_VOTED, COULD_NOT_FIND, INVALID_ANSWER
from core.lib import clean_graphql_input
from core.resolvers import shared

from ..models import Poll, PollChoice


def resolve_add_poll(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    entity = Poll()

    entity.owner = user

    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    entity.save()

    for choice in clean_input.get("choices"):
        PollChoice.objects.create(poll=entity, text=choice)

    return {
        "entity": entity
    }


def resolve_edit_poll(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        entity = Poll.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(entity, user)

    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

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

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

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

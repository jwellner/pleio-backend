from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import NOT_LOGGED_IN, INVALID_SUBTYPE
from core.models import Entity
from core.resolvers.mutation_edit_comment import resolve_edit_comment
from blog.resolvers.mutation import resolve_edit_blog
from discussion.resolvers.mutation import resolve_edit_discussion
from activity.resolvers.mutation import resolve_edit_status_update
from event.resolvers.mutation_event_edit import resolve_edit_event
from task.resolvers.mutation import resolve_edit_task
from wiki.resolvers.mutation import resolve_edit_wiki
from news.resolvers.mutation import resolve_edit_news
from question.resolvers.mutation import resolve_edit_question


def resolve_edit_entity(_, info, input, draft=False):
    # pylint: disable=redefined-builtin

    clean_input = clean_graphql_input(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        # TODO: update frontend to use editComment
        return resolve_edit_comment(_, info, input)

    if entity._meta.model_name == "blog":
        return resolve_edit_blog(_, info, input, draft)

    if entity._meta.model_name == "event":
        return resolve_edit_event(_, info, input)

    if entity._meta.model_name == "discussion":
        return resolve_edit_discussion(_, info, input)

    if entity._meta.model_name == "statusupdate":
        return resolve_edit_status_update(_, info, input)

    if entity._meta.model_name == "task":
        return resolve_edit_task(_, info, input)

    if entity._meta.model_name == "wiki":
        return resolve_edit_wiki(_, info, input, draft)

    if entity._meta.model_name == "news":
        return resolve_edit_news(_, info, input, draft)

    if entity._meta.model_name == "question":
        return resolve_edit_question(_, info, input)

    raise GraphQLError(INVALID_SUBTYPE)

from graphql import GraphQLError
from core.lib import clean_graphql_input
from core.constances import INVALID_SUBTYPE
from core.resolvers.mutation_add_comment import resolve_add_comment
from blog.resolvers.mutation import resolve_add_blog
from discussion.resolvers.mutation import resolve_add_discussion
from activity.resolvers.mutation import resolve_add_status_update
from event.resolvers.mutation_event_add import resolve_add_event
from task.resolvers.mutation import resolve_add_task
from file.resolvers.mutation import resolve_add_folder
from wiki.resolvers.mutation import resolve_add_wiki
from news.resolvers.mutation import resolve_add_news
from question.resolvers.mutation import resolve_add_question

def resolve_add_entity(_, info, input):
    # pylint: disable=redefined-builtin

    clean_input = clean_graphql_input(input)

    if clean_input.get("subtype") == "blog":
        return resolve_add_blog(_, info, input)
    if clean_input.get("subtype") == "comment":
        return resolve_add_comment(_, info, input)
    if clean_input.get("subtype") == "event":
        return resolve_add_event(_, info, input)
    if clean_input.get("subtype") == "discussion":
        return resolve_add_discussion(_, info, input)
    if clean_input.get("subtype") in ["status_update", "thewire"]:
        return resolve_add_status_update(_, info, input)
    if clean_input.get("subtype") == "task":
        return resolve_add_task(_, info, input)
    if clean_input.get("subtype") == "folder":
        return resolve_add_folder(_, info, input)
    if clean_input.get("subtype") == "wiki":
        return resolve_add_wiki(_, info, input)
    if clean_input.get("subtype") == "news":
        return resolve_add_news(_, info, input)
    if clean_input.get("subtype") == "question":
        return resolve_add_question(_, info, input)

    raise GraphQLError(INVALID_SUBTYPE)

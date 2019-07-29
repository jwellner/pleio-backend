from ariadne import ObjectType
import reversion
from graphql import GraphQLError
from ..lib import get_type, get_id
from ..constances import NOT_LOGGED_IN
from news.models import News
from poll.models import Poll
from discussion.models import Discussion
from event.models import Event
from question.models import Question
from wiki.models import Wiki
from cms.models import CmsPage
from blog.models import Blog

mutation = ObjectType("Mutation")

@mutation.field("addEntity")
def resolve_add_entity(_, info, input):
    # pylint: disable=redefined-builtin

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    result = None

    if input.get("subtype") == "news":
        with reversion.create_revision():
            result = News.objects.create(
                title=input.get("title"),
                description=input.get("description"),
                owner=info.context.user,
                tags=input.get("tags")
            )

            result.save()

            reversion.set_user(info.context.user)
            reversion.set_comment("addEntity mutation")

    elif input.get("subtype") == "blog":
        with reversion.create_revision():
            result = Blog.objects.create(
                title=input.get("title"),
                description=input.get("description"),
                owner=info.context.user,
            )

            result.save()

            reversion.set_user(info.context.user)
            reversion.set_comment("addEntity mutation")

    else:
        raise GraphQLError("invalid_subtype")

    return {
        "entity": result
    }

@mutation.field("editEntity")
def resolve_edit_entity(_, info, input):
    # pylint: disable=redefined-builtin

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    subtype = get_type(input.get("guid"))
    entity_id = get_id(input.get("guid"))

    if subtype == "news":
        objects = News.objects
    elif subtype == "poll":
        objects = Poll.objects
    elif subtype == "discussion":
        objects = Discussion.objects
    elif subtype == "event":
        objects = Event.objects
    elif subtype == "wiki":
        objects = Wiki.objects
    elif subtype == "question":
        objects = Question.objects
    elif subtype == "page":
        objects = CmsPage.objects
    elif subtype == "blog":
        objects = Blog.objects
    else:
        return None

    entity = objects.get(id=entity_id)

    if (entity) :
        with reversion.create_revision():
            entity.title = input.get("title")
            entity.description = input.get("description")
            entity.tags = input.get("tags")

            entity.save()

            reversion.set_user(info.context.user)
            reversion.set_comment("editEntity mutation")
    else :
        return None

    return {
        "entity": entity
    }

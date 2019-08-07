from ariadne import ObjectType
import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_SUBTYPE
from news.models import News
from poll.models import Poll
from discussion.models import Discussion
from event.models import Event
from question.models import Question
from wiki.models import Wiki
from cms.models import CmsPage
from blog.models import Blog
from .mutation_add_group import resolve_add_group
from .mutation_edit_group import resolve_edit_group
from .mutation_join_group import resolve_join_group
from .mutation_leave_group import resolve_leave_group
from .mutation_add_entity import resolve_add_entity
from .mutation_edit_entity import resolve_edit_entity


mutation = ObjectType("Mutation")
mutation.set_field("addGroup", resolve_add_group)
mutation.set_field("editGroup", resolve_edit_group)
mutation.set_field("joinGroup", resolve_join_group)
mutation.set_field("leaveGroup", resolve_leave_group)

mutation.set_field("addEntity", resolve_add_entity)
mutation.set_field("editEntity", resolve_edit_entity)

@mutation.field("deleteEntity")
def resolve_delete_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    subtype = get_type(input.get("guid"))
    entity_id = get_id(input.get("guid"))

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
        entity.delete()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        'success': True
    }

def get_model_by_subtype(subtype):
    model = None

    if subtype == "news":
        model = News
    elif subtype == "poll":
        model = Poll
    elif subtype == "discussion":
        model = Discussion
    elif subtype == "event":
        model = Event
    elif subtype == "wiki":
        model = Wiki
    elif subtype == "question":
        model = Question
    elif subtype == "page":
        model = CmsPage
    elif subtype == "blog":
        model = Blog

    return model
        
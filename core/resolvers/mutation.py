from ariadne import ObjectType
import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from ..lib import get_type, get_id
from ..constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_SUBTYPE
from ..enums import ACCESS_TYPE
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

    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    model = get_model_by_subtype(input.get("subtype"))

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    acl_read = [ACCESS_TYPE.user.format(user.id)] # owner can always read

    if input.get("accessId") == 1:
        acl_read.append(ACCESS_TYPE.logged_in)
    elif input.get("accessId") == 2:
        acl_read.append(ACCESS_TYPE.public)

    acl_write = [ACCESS_TYPE.user.format(user.id)]

    with reversion.create_revision():
        # default fiels
        entity = model()
        entity.title = input.get("title")
        entity.description = input.get("description")
        entity.owner = user
        entity.tags = input.get("tags")
        entity.read_access = acl_read
        entity.write_access = acl_write

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("addEntity mutation")

    return {
        "entity": entity
    }

@mutation.field("editEntity")
def resolve_edit_entity(_, info, input):
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

    acl_read = [ACCESS_TYPE.user.format(entity.owner.id)] # owner can always read

    if input.get("accessId") == 1:
        acl_read.append(ACCESS_TYPE.logged_in)
    elif input.get("accessId") == 2:
        acl_read.append(ACCESS_TYPE.public)

    with reversion.create_revision():
        entity.title = input.get("title")
        entity.description = input.get("description")
        entity.owner = user
        entity.tags = input.get("tags")
        entity.read_access = acl_read

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }

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
        
from ariadne import ObjectType, InterfaceType
from ..enums import ORDER_DIRECTION, ORDER_BY
from ..models import Object, Group, User
from ..lib import get_type, get_id
from ..constances import NOT_LOGGED_IN
from news.models import News
from poll.models import Poll
from discussion.models import Discussion
from event.models import Event
from question.models import Question
from wiki.models import Wiki
from cms.models import CmsPage
import logging
import reversion
from graphql import GraphQLError
from .mutation import mutation
from .query import query
from ..enums import ACCESS_TYPE

logger = logging.getLogger('django')

viewer = ObjectType("Viewer")
entity = InterfaceType("Entity")

@entity.type_resolver
def resolve_entity_type(obj, *_):
    return obj._meta.object_name

@viewer.field('user')
def resolve_user(_, info):
    user = info.context.user

    if user.is_authenticated:
        return user
    return None

# default entity resolvers 
def resolve_entity_access_id(obj, info):
    # pylint: disable=unused-argument

    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0

def resolve_entity_write_access_id(obj, info):
    # pylint: disable=unused-argument

    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0

def resolve_entity_can_edit(obj, info):
    return obj.can_write(info.context.user)


resolvers = [query, viewer, entity, mutation]

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
from actstream import action
from .mutation import mutation
from .query import query

logger = logging.getLogger('django')

viewer = ObjectType("Viewer")
entity = InterfaceType("Entity")

@entity.type_resolver
def resolve_entity_type(obj, *_):
    print(obj._meta.object_name)
    return obj._meta.object_name


@viewer.field('user')
def resolve_user(_, info):
    user = info.context.user

    if user.is_authenticated:
        return {
            'guid': user.guid,
            'username': user.guid,
            'name': user.get_short_name()
        }
    return None

resolvers = [query, viewer, entity, mutation]

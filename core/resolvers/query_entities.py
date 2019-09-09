from django.db.models import Q
from core.constances import ORDER_DIRECTION, ORDER_BY
from core.models import Entity
from news.models import News
from poll.models import Poll
from discussion.models import Discussion
from event.models import Event
from question.models import Question
from wiki.models import Wiki
from cms.models import CmsPage
from blog.models import Blog

def conditional_group_filter(container_guid):

    if container_guid:
        return Q(group__id=container_guid)

    return Q()

def resolve_entities(
    _,
    info,
    offset=0,
    limit=20,
    type=None,
    subtype=None,
    subtypes=None,
    containerGuid=None,
    tags=None,
    orderBy=ORDER_BY.timeCreated,
    orderDirection=ORDER_DIRECTION.asc,
    addFeatured=False,
    isFeatured=False
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

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
    elif subtype is None:
        objects = Entity.objects
    else:
        return None

    if orderBy == ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ORDER_BY.lastAction:
        order_by = 'updated_at'
    else:
        order_by = 'created_at'
    
    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    entities = objects.visible(info.context.user)
    entities = entities.filter(conditional_group_filter(containerGuid))
    entities = entities.order_by(order_by)
    entities = entities[offset:offset+limit]

    return {
        'total': entities.count(),
        'canWrite': False,
        'edges': entities,
    }

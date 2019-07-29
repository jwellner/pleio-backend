from ariadne import ObjectType
from ..enums import ORDER_DIRECTION, ORDER_BY
from ..models import Object, Group, User
from ..lib import get_type, get_id
from news.models import News
from poll.models import Poll
from discussion.models import Discussion
from event.models import Event
from question.models import Question
from wiki.models import Wiki
from cms.models import CmsPage
from blog.models import Blog
import logging

logger = logging.getLogger('django')

query = ObjectType("Query")

@query.field("site")
def resolve_site(*_):
    return {
        'guid': '1',
        'name': 'Pleio 3.0',
        'theme': 'Pleio',
        'menu': [
            {
                'title': 'News',
                'link': '/news',
                'children': []
            },
            {
                'title': 'Blog',
                'link': '/blog',
                'children': []
            },
            {
                'title': 'Discussion',
                'link': '/discussion',
                'children': []
            },
            {
                'title': 'Events',
                'link': '/events',
                'children': []
            },
            {
                'title': 'Groups',
                'link': '/groups',
                'children': []
            },
            {
                'title': 'Wiki',
                'link': '/wiki',
                'children': []
            },
            {
                'title': 'Questions',
                'link': '/questions',
                'children': []
            },
            {
                'title': 'Polls',
                'link': '/polls',
                'children': []
            }
        ],
        'profile': [],
        'footer': [],
        'directLinks': [],
        'accessIds': [],
        'defaultAccessId': 0,
        'logo': None,
        'logoAlt': '',
        'icon': '',
        'iconAlt': '',
        'showIcon': False,
        'startpage': None,
        'showLeader': False,
        'showLeaderButtons': False,
        'subtitle': '',
        'leaderImage': '',
        'showInitiative': True,
        'initiativeTitle': '',
        'inititativeImageAlt': '',
        'inititativeDescription': '',
        'initiatorLink': '',
        'style': {
            'font': 'Arial',
            'colorPrimary': '#0e2f56',
            'colorSecondary': '#118df0',
            'colorHeader': 'red'
        },
        'customTagsAllowed': True,
        'tagCategories': [],
        'activityFilter': {
            'contentTypes': [
                {
                    'key': 'event',
                    'value': 'Agenda-Item'
                },
                {
                    'key': 'blog',
                    'value': 'Blog'
                },
                {
                    'key': 'discussion',
                    'value': 'Discussie'
                },
                {
                    'key': 'news',
                    'value': 'Nieuws'
                },
                {
                    'key': 'statusupdate',
                    'value': 'Update'
                },
                {
                    'key': 'question',
                    'value': 'Vraag'
                },   
            ]
        },
        'showExtraHomepageFilters': False,
        'usersOnline': 1,
        'achievementsEnabled': True,
    }


@query.field("viewer")
def resolve_viewer(_, info):
    user = info.context.user

    if not user.is_authenticated:
        return {
            'guid': '0',
            'loggedIn': False,
            'isSubEditor': False,
            'isAdmin': False,
            'tags': [],
            'canWriteToContainer': False,
            'user': {
                'guid': '0'
            }
        }

    return {
        'guid': user.guid,
        'loggedIn': True,
        'isSubEditor': False,
        'isAdmin': user.is_admin,
        'tags': [],
        'canWriteToContainer': True,
    }


@query.field("entities")
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
        objects = Object.objects
    else:
        return None

    entities = objects.all()[offset:offset+limit]

    return {
        'total': entities.count(),
        'canWrite': False,
        'edges': entities,
    }


@query.field("entity")
def resolve_entity(
    _,
    info,
    guid
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    subtype = get_type(guid)
    entity_id = get_id(guid)

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

    return entity

# TODO: Implement search


@query.field("search")
def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    return {
        'total': 0,
        'totals': [],
        'edges': []
    }

# TODO: Implement recommended


@query.field("recommended")
def resolve_recommended(_, info, offset=0, limit=20):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'canWrite': False,
        'edges': []
    }

# TODO: Implement trending


@query.field("trending")
def resolve_trending(_, info):
    # pylint: disable=unused-argument
    return [
        {'tag': 'pleio', 'likes': 10},
        {'tag': 'backend2', 'likes': 3}
    ]

# TODO: Implement top


@query.field("top")
def resolve_top(_, info):
    # pylint: disable=unused-argument
    user = info.context.user

    if user.is_authenticated:
        return [
            {'user': user, 'likes': 42}
        ]

    return []

# TODO: Implement breadcrumb


@query.field("breadcrumb")
def resolve_breadcrumb(_, info, guid=None):
    # pylint: disable=unused-argument
    return []


@query.field("groups")
def resolve_groups(
    _,
    info,
    q=None,
    filter=None,
    offset=0,
    limit=20
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    groups = []

    if q:
        groups = Group.objects.get(title__contains=q)[offset, offset+limit]
    else:
        groups = Group.objects.all()[offset:offset+limit]

    return {
        'total': groups.count(),
        'canWrite': False,
        'edges': groups
    }

@query.field('users')
def resolve_users(_, info, q=None, filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    user = info.context.user

    if not user.is_authenticated:
        return None

    users = []

    if q:
        users = User.objects.filter(name__icontains=q)[offset:offset+limit]
    else:
        users = User.objects.all()[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': users,
        'filterCount': None
    }


@query.field('filters')
def resolve_filters(_, info):
    # pylint: disable=unused-argument
    return {
        'users': None
    }

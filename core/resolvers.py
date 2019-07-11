from ariadne import ObjectType
from .enums import ORDER_DIRECTION, ORDER_BY

query = ObjectType("Query")
viewer = ObjectType("Viewer")


@query.field("site")
def resolve_site(*_):
    return {
        'guid': '1',
        'name': 'Backend2',
        'theme': 'Backend2',
        'menu': [],
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
        'showInitiative': False,
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
        'customTagsAllowed': False,
        'tagCategories': [],
        'activityFilter': {
            'contentTypes': []
        },
        'showExtraHomepageFilters': False,
        'usersOnline': 1
    }


@query.field("viewer")
def resolve_viewer(_, info):

    if not info.context.user.is_authenticated:
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

    user = info.context.user

    return {
        'guid': user.guid(),
        'loggedIn': True,
        'isSubEditor': False,
        'isAdmin': user.is_admin,
        'tags': [],
        'canWriteToContainer': False,
    }


@query.field("entities")
def resolve_entities(
    _,
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
    return {
        'total': 0,
        'canWrite': False,
        'edges': []
    }


@viewer.field('user')
def resolve_user(_, info):
    user = info.context.user

    if user.is_authenticated:
        return {
            'guid': user.guid(),
            'username': user.get_full_name(),
            'name': user.get_short_name()
        }
    return None


resolvers = [query, viewer]

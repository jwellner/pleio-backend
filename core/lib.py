from core.constances import ACCESS_TYPE
from core import config
from django.conf import settings
from django.apps import apps
from django.utils.text import slugify
import os

def get_acl(user):
    """Get user Access List"""

    acl = set([ACCESS_TYPE.public])

    if user.is_authenticated:
        acl.add(ACCESS_TYPE.logged_in)
        acl.add(ACCESS_TYPE.user.format(user.id))

        if user.memberships:
            groups = set(
                ACCESS_TYPE.group.format(membership.group.id) for membership in user.memberships.filter(type__in=['admin', 'owner', 'member'])
                )
            acl = acl.union(groups)

    return acl


def get_type(guid):
    """Get content type from guid"""

    splitted_id = guid.split(':')
    return splitted_id[0]


def get_id(guid):
    """Get content id from guid"""

    splitted_id = guid.split(':')
    return splitted_id[1]


def remove_none_from_dict(values):
    """Cleanup resolver input: remove keys with None values"""

    return {k:v for k,v in values.items() if v is not None}


def webpack_dev_server_is_available():
    """Return true when webpack developer server is available"""

    if settings.ENV == 'prod':
        return False

    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            return s.connect_ex(('host.docker.internal', 9001)) == 0
        except Exception:
            return False


def get_access_ids(obj=None):
    """Return the available accessId's"""
    accessIds = []
    accessIds.append({ 'id': 0, 'description': 'Alleen eigenaar'})
    accessIds.append({ 'id': 1, 'description': 'Gebruikers van deze site'})
    accessIds.append({ 'id': 2, 'description': 'Iedereen (publiek zichtbaar)'})

    if isinstance(obj, apps.get_model('core.Group')):
        accessIds.append({ 'id': 4, 'description': "Group: {}".format(obj.name)})

    return accessIds

def get_activity_filters():
    """TODO: should only return active content"""
    return {
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
    }

def get_settings():
    """Temporary helper to build window.__SETTINGS__"""

    return {
        "site": get_site(),
        "env": settings.ENV,
        "odtEnabled": False,
        "enableSharing": False,
        "showUpDownVoting": False,
        "externalLogin": True,
        "advancedPermissions": True,
        "groupMemberExport": False,
        "showExcerptInNewsCard": False,
        "showTagInNewsCard": False,
        "numberOfFeaturedItems": 2,
        "enableFeedSorting": True,
        "commentsOnNews": True,
        "eventExport": False,
        "subgroups": False,
        "statusUpdateGroups": True,
        "showExtraHomepageFilters": True,
    }

def get_site():
    site = {
        'guid': 1,
        'name': config.NAME,
        'theme': config.THEME,
        'menu': config.MENU,
        'profile': [],
        'footer': config.FOOTER,
        'directLinks': config.DIRECT_LINKS,
        'accessIds': get_access_ids(),
        'defaultAccessId': config.DEFAULT_ACCESS_ID,
        'logo': config.LOGO,
        'logoAlt': config.LOGO_ALT,
        'icon': config.ICON,
        'iconAlt': config.ICON_ALT,
        'showIcon': config.ICON_ENABLED,
        'startpage': config.STARTPAGE,
        'showLeader': config.LEADER_ENABLED,
        'showLeaderButtons': config.LEADER_BUTTONS_ENABLED,
        'subtitle': config.SUBTITLE,
        'leaderImage': config.LEADER_IMAGE,
        'showInitiative': config.INITIATIVE_ENABLED,
        'initiativeTitle': config.INITIATIVE_TITLE,
        'inititativeImageAlt': config.INITIATIVE_IMAGE_ALT,
        'inititativeDescription': config.INITIATIVE_DESCRIPTION,
        'initiatorLink': config.INITIATOR_LINK,
        'style': config.STYLE,
        'customTagsAllowed': config.CUSTOM_TAGS_ENABLED,
        'tagCategories': config.TAG_CATEGORIES,
        'activityFilter': get_activity_filters(),
        'showExtraHomepageFilters': config.ACTIVITY_FEED_FILTERS_ENABLED,
        'usersOnline': 1,
        'achievementsEnabled': config.ACHIEVEMENTS_ENABLED,
        'cancelMembershipEnabled': config.CANCEL_MEMBERSHIP_ENABLED,
    }

    return site

def generate_object_filename(obj, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join(str(obj.id), filename)

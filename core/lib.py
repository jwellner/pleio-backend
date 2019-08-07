from core.constances import ACCESS_TYPE
from django.conf import settings
from django.apps import apps

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

    accessIds = []
    accessIds.append({ 'id': 0, 'description': 'Alleen eigenaar'})
    accessIds.append({ 'id': 1, 'description': 'Gebruikers van deze site'})
    accessIds.append({ 'id': 2, 'description': 'Iedereen (publiek zichtbaar)'})

    if isinstance(obj, apps.get_model('core.Group')):
        accessIds.append({ 'id': 4, 'description': "Group: {}".format(obj.name)})

    return accessIds


def get_settings():
    """Temporary helper to build window.__SETTINGS__"""

    return {
        "site": {
            "guid": 1,
            "name": "Pleio standalone",
            "accessIds": get_access_ids(),
            "defaultAccessId": "1",
            "startPage": "activity",
            "startPageCms": "1",
            "likeIcon": "heart",
            "newsletter": True,
            "theme": "leraar",
            "isClosed": False,
            "cookieConsent": False,
            "limitedGroupAdd": "no",
            "customTagsAllowed": False,
        },
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
        "commentsOnNews": False,
        "eventExport": False,
        "subgroups": False,
        "statusUpdateGroups": True,
        "showExtraHomepageFilters": True,
    }

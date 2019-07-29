from django.conf import settings


def webpack_dev_server_is_available():
    if settings.ENV == 'prod':
        return False

    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            return s.connect_ex(('host.docker.internal', 9001)) == 0
        except Exception:
            return False

def get_settings():
    return {
        "site": {
            "guid": 1,
            "name": "Pleio standalone",
            "accessIds": [
                {
                    "id": 0,
                    "description": "Alleen de eigenaar"
                }, 
                {
                    "id": 1,
                    "description": "Gebruikers van deze site"
                },
                {
                    "id": 2,
                    "description": "Iedereen (publiek zichtbaar)"
                }
            ],
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

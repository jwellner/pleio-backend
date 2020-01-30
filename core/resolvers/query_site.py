from core import config
from core.lib import get_access_ids, get_activity_filters
from core.models import UserProfile
from django.conf import settings
from django.utils import timezone

def get_online_users():
    ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
    return UserProfile.objects.filter(last_online__gte=ten_minutes_ago).count()

def get_settings():
    """Temporary helper to build window.__SETTINGS__"""

    return {
        "site": get_site(),
        "env": settings.ENV,
        "odtEnabled": False,
        "enableSharing": True,
        "showUpDownVoting": True,
        "externalLogin": True,
        "advancedPermissions": True,
        "groupMemberExport": False,
        "showExcerptInNewsCard": True,
        "showTagInNewsCard": True,
        "numberOfFeaturedItems": 3,
        "enableFeedSorting": True,
        "commentsOnNews": True,
        "eventExport": True,
        "subgroups": True,
        "statusUpdateGroups": True,
        "showExtraHomepageFilters": True,
        'showViewsCount': True
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
        'language': config.LANGUAGE,
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
        'usersOnline': get_online_users(),
        'achievementsEnabled': config.ACHIEVEMENTS_ENABLED,
        'cancelMembershipEnabled': config.CANCEL_MEMBERSHIP_ENABLED,
    }

    return site

def resolve_site(*_):
    return get_site()

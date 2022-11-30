from django.conf import settings
from core import config
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import get_access_ids
from core.models import SiteStat
from graphql import GraphQLError


def get_start_page(user):
    if user.is_anonymous and config.ANONYMOUS_START_PAGE:
        return {
            "startPage": config.ANONYMOUS_START_PAGE,
            "startPageCms": config.ANONYMOUS_START_PAGE_CMS,
        }
    return {
        "startPage": config.STARTPAGE,
        "startPageCms": config.STARTPAGE_CMS,
    }


def get_settings(user):
    """Temporary helper to build window.__SETTINGS__"""

    return {
        "site": {
            "language": config.LANGUAGE,
            "name": config.NAME,
            "theme": config.THEME,
            "accessIds": get_access_ids(),
            "defaultAccessId": config.DEFAULT_ACCESS_ID,
            "likeIcon": config.LIKE_ICON,
            "limitedGroupAdd": config.LIMITED_GROUP_ADD,
            "cookieConsent": config.COOKIE_CONSENT,
            "isClosed": config.IS_CLOSED,
            "newsletter": config.NEWSLETTER,
            **get_start_page(user),
        },
        "backendVersion": config.BACKEND_VERSION,
        "env": settings.ENV,
        "odtEnabled": False,
        "enableSharing": config.ENABLE_SHARING,
        "showUpDownVoting": config.SHOW_UP_DOWN_VOTING,
        "externalLogin": True,
        "groupMemberExport": config.GROUP_MEMBER_EXPORT,
        "showExcerptInNewsCard": config.SHOW_EXCERPT_IN_NEWS_CARD,
        "numberOfFeaturedItems": config.NUMBER_OF_FEATURED_ITEMS,
        "enableFeedSorting": config.ENABLE_FEED_SORTING,
        "commentsOnNews": config.COMMENT_ON_NEWS,
        "eventExport": config.EVENT_EXPORT,
        'eventTiles': config.EVENT_TILES,
        "subgroups": config.SUBGROUPS,
        "statusUpdateGroups": config.STATUS_UPDATE_GROUPS,
        "showExtraHomepageFilters": config.ACTIVITY_FEED_FILTERS_ENABLED,
        "showViewsCount": config.SHOW_VIEW_COUNT,
        "showLoginRegister": config.SHOW_LOGIN_REGISTER,
        'kalturaVideoEnabled': config.KALTURA_VIDEO_ENABLED,
        'kalturaVideoPartnerId': config.KALTURA_VIDEO_PARTNER_ID,
        'kalturaVideoPlayerId': config.KALTURA_VIDEO_PLAYER_ID,
        'showSuggestedItems': config.SHOW_SUGGESTED_ITEMS,
        'pdfCheckerEnabled': config.PDF_CHECKER_ENABLED,
        'maxCharactersInAbstract': config.MAX_CHARACTERS_IN_ABSTRACT,
        'collabEditingEnabled': config.COLLAB_EDITING_ENABLED,
        'preserveFileExif': config.PRESERVE_FILE_EXIF,
    }


def resolve_site(*_):
    return {'guid': 1}


def resolve_site_settings(_, info):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    return {}


def resolve_site_stats(_, info):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    try:
        db_usage = SiteStat.objects.filter(stat_type='DB_SIZE').latest('created_at').value
    except Exception:
        db_usage = 0

    try:
        file_disk_usage = SiteStat.objects.filter(stat_type='DISK_SIZE').latest('created_at').value
    except Exception:
        file_disk_usage = 0

    return {
        'dbUsage': db_usage,
        'fileDiskUsage': file_disk_usage
    }

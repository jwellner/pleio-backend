from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from django.templatetags.static import static
from cms.models import Page
from core import config
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN
from core.lib import get_access_ids, get_activity_filters, get_exportable_user_fields
from core.models import UserProfile, ProfileField
from graphql import GraphQLError


def get_online_users():
    ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
    return UserProfile.objects.filter(last_online__gte=ten_minutes_ago).count()


def get_settings():
    """Temporary helper to build window.__SETTINGS__"""

    return {
        "site": get_site(),
        "backendVersion": config.BACKEND_VERSION,
        "env": settings.ENV,
        "odtEnabled": False,
        "enableSharing": config.ENABLE_SHARING,
        "showUpDownVoting": config.SHOW_UP_DOWN_VOTING,
        "externalLogin": True,
        "advancedPermissions": config.ADVANCED_PERMISSIONS_ENABLED,
        "groupMemberExport": config.GROUP_MEMBER_EXPORT,
        "showExcerptInNewsCard": config.SHOW_EXCERPT_IN_NEWS_CARD,
        "numberOfFeaturedItems": config.NUMBER_OF_FEATURED_ITEMS,
        "enableFeedSorting": config.ENABLE_FEED_SORTING,
        "commentsOnNews": config.COMMENT_ON_NEWS,
        "eventExport": config.EVENT_EXPORT,
        "subgroups":  config.SUBGROUPS,
        "statusUpdateGroups": config.STATUS_UPDATE_GROUPS,
        "showExtraHomepageFilters": config.ACTIVITY_FEED_FILTERS_ENABLED,
        "showViewsCount": config.ADVANCED_PERMISSIONS_ENABLED,
        "showLoginRegister": config.SHOW_LOGIN_REGISTER,
    }


def get_site():

    site = {
        'guid': 1,
        'name': config.NAME,
        'theme': config.THEME,
        'menu': config.MENU,
        'profile': config.PROFILE,
        'footer': config.FOOTER,
        'directLinks': config.DIRECT_LINKS,
        'accessIds': get_access_ids(),
        # TODO: implement isClosed when functionality is available
        'isClosed': False,
        'defaultAccessId': config.DEFAULT_ACCESS_ID,
        'language': config.LANGUAGE,
        'logo': config.LOGO,
        'logoAlt': config.LOGO_ALT,
        'likeIcon': config.LIKE_ICON,
        'icon': config.ICON if config.ICON else static('icon.svg'),
        'iconAlt': config.ICON_ALT,
        'showIcon': config.ICON_ENABLED,
        'startPage': config.STARTPAGE,
        'startPageCms': config.STARTPAGE_CMS,
        'showLeader': config.LEADER_ENABLED,
        'showLeaderButtons': config.LEADER_BUTTONS_ENABLED,
        'subtitle': config.SUBTITLE,
        'leaderImage': config.LEADER_IMAGE,
        'showInitiative': config.INITIATIVE_ENABLED,
        'initiativeTitle': config.INITIATIVE_TITLE,
        'inititativeImageAlt': config.INITIATIVE_IMAGE_ALT,
        'inititativeDescription': config.INITIATIVE_DESCRIPTION,
        'initiatorLink': config.INITIATOR_LINK,
        'style': {
            'font': config.FONT,
            'colorPrimary': config.COLOR_PRIMARY,
            'colorSecondary': config.COLOR_SECONDARY,
            'colorHeader': get_color_header(),
        },
        'customTagsAllowed': config.CUSTOM_TAGS_ENABLED,
        'tagCategories': config.TAG_CATEGORIES,
        'showTagsInFeed': config.SHOW_TAGS_IN_FEED,
        'showTagsInDetail': config.SHOW_TAGS_IN_DETAIL,
        'activityFilter': get_activity_filters(),
        'showExtraHomepageFilters': config.ACTIVITY_FEED_FILTERS_ENABLED,
        'usersOnline': get_online_users(),
        'achievementsEnabled': config.ACHIEVEMENTS_ENABLED,
        'limitedGroupAdd': config.LIMITED_GROUP_ADD,
        'cancelMembershipEnabled': config.CANCEL_MEMBERSHIP_ENABLED,
        'newsletter': config.NEWSLETTER,
        'showLoginRegister': config.SHOW_LOGIN_REGISTER,
    }

    return site

def get_site_settings():

    defaultAccessIdOptions = [
            {"value": 0, "label": ugettext_lazy("Just me")},
            {"value": 1, "label": ugettext_lazy("Logged in users")}
        ]

    if not config.IS_CLOSED:
        defaultAccessIdOptions.append({"value": 2, "label": ugettext_lazy("Public")})

    start_page_cms_options = []
    for page in Page.objects.all().order_by('title'):
        start_page_cms_options.append({"value": page.guid, "label": page.title})

    site_settings = {
        'guid': 1,
        'name': config.NAME,
        'description': config.DESCRIPTION,
        'language': config.LANGUAGE,
        'languageOptions': [{'value': 'nl', 'label': ugettext_lazy('Dutch')}, {'value': 'en', 'label': ugettext_lazy('English')}],
        'isClosed': config.IS_CLOSED,
        'allowRegistration': config.ALLOW_REGISTRATION,
        'defaultAccessId': config.DEFAULT_ACCESS_ID,
        'defaultAccessIdOptions': defaultAccessIdOptions,

        'googleAnalyticsUrl': config.GOOGLE_ANALYTICS_URL,
        'googleSiteVerification': config.GOOGLE_SITE_VERIFICATION,
        'piwikUrl': config.PIWIK_URL,
        'piwikId': config.PIWIK_ID,

        'font': config.FONT,
        'colorPrimary': config.COLOR_PRIMARY,
        'colorSecondary': config.COLOR_SECONDARY,
        'colorHeader': get_color_header(),
        'theme': config.THEME,
        'themeOptions': config.THEME_OPTIONS,
        'fontOptions': [
            {"value": "Rijksoverheid Sans", "label": "Rijksoverheid Sans"},
            {"value": "Roboto", "label": "Roboto"},
            {"value": "Source Sans Pro", "label": "Source Sans Pro"}
        ],
        'logo': config.LOGO,
        'logoAlt': config.LOGO_ALT,
        'likeIcon': config.LIKE_ICON,

        'startPageOptions': [{"value": "activity", "label": ugettext_lazy("Activity stream")},{"value": "cms", "label": ugettext_lazy("CMS page")}],
        'startPage': config.STARTPAGE,

        'startPageCmsOptions': start_page_cms_options,
        'startPageCms': config.STARTPAGE_CMS,
        'icon': config.ICON if config.ICON else static('icon.svg'),
        'showIcon': config.ICON_ENABLED,
        'menu': config.MENU,

        "numberOfFeaturedItems": config.NUMBER_OF_FEATURED_ITEMS,
        "enableFeedSorting": config.ENABLE_FEED_SORTING,
        'showExtraHomepageFilters': config.ACTIVITY_FEED_FILTERS_ENABLED,
        'showLeader': config.LEADER_ENABLED,
        'showLeaderButtons': config.LEADER_BUTTONS_ENABLED,
        'subtitle': config.SUBTITLE,
        'leaderImage': config.LEADER_IMAGE,
        'showInitiative': config.INITIATIVE_ENABLED,
        'initiativeTitle': config.INITIATIVE_TITLE,
        'initiativeDescription': config.INITIATIVE_DESCRIPTION,
        'initiativeImage': config.INITIATIVE_IMAGE,
        'initiativeImageAlt': config.INITIATIVE_IMAGE_ALT,
        'initiativeLink': config.INITIATIVE_LINK,
        'directLinks': config.DIRECT_LINKS,
        'footer': config.FOOTER,

        'profile': get_profile(),

        'tagCategories': config.TAG_CATEGORIES,
        'showTagsInFeed': config.SHOW_TAGS_IN_FEED,
        'showTagsInDetail': config.SHOW_TAGS_IN_DETAIL,

        'defaultEmailOverviewFrequencyOptions': [
            {"value": "daily", "label": ugettext_lazy("Daily")},
            {"value": "weekly", "label": ugettext_lazy("Weekly")},
            {"value": "monthly", "label": ugettext_lazy("Monthly")},
            {"value": "never", "label": ugettext_lazy("Never")}
        ],
        'defaultEmailOverviewFrequency': config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY,
        'emailOverviewSubject': config.EMAIL_OVERVIEW_SUBJECT,
        'emailOverviewTitle': config.EMAIL_OVERVIEW_TITLE,
        'emailOverviewIntro': config.EMAIL_OVERVIEW_INTRO,
        'emailOverviewEnableFeatured': config.EMAIL_OVERVIEW_ENABLE_FEATURED,
        'emailOverviewFeaturedTitle': config.EMAIL_OVERVIEW_FEATURED_TITLE,
        'emailNotificationShowExcerpt': config.EMAIL_NOTIFICATION_SHOW_EXCERPT,

        'exportableUserFields': get_exportable_user_fields(),

        'showLoginRegister': config.SHOW_LOGIN_REGISTER,
        'customTagsAllowed': config.CUSTOM_TAGS_ENABLED,
        'showUpDownVoting': config.SHOW_UP_DOWN_VOTING,
        'enableSharing': config.ENABLE_SHARING,
        'showViewsCount': config.SHOW_VIEW_COUNT,
        'newsletter': config.NEWSLETTER,
        'cancelMembershipEnabled': config.CANCEL_MEMBERSHIP_ENABLED,
        'advancedPermissions': config.ADVANCED_PERMISSIONS_ENABLED,
        'showExcerptInNewsCard': config.SHOW_EXCERPT_IN_NEWS_CARD,
        'commentsOnNews': config.COMMENT_ON_NEWS,
        'eventExport': config.EVENT_EXPORT,
        'questionerCanChooseBestAnswer': config.QUESTIONER_CAN_CHOOSE_BEST_ANSWER,
        'statusUpdateGroups': config.STATUS_UPDATE_GROUPS,
        'subgroups': config.SUBGROUPS,
        'groupMemberExport': config.GROUP_MEMBER_EXPORT,
        'limitedGroupAdd': config.LIMITED_GROUP_ADD,

        'accessIds': get_access_ids(),
        'startpage': config.STARTPAGE,
        'initiatorLink': config.INITIATOR_LINK,

        'activityFilter': get_activity_filters(),

        'usersOnline': get_online_users(),
        'achievementsEnabled': config.ACHIEVEMENTS_ENABLED,
    }

    return site_settings

def get_color_header():
    if not config.COLOR_HEADER:
        return config.COLOR_PRIMARY
    return config.COLOR_HEADER

def get_profile():
    profile_fields = []
    for field in config.PROFILE:
        try:
            profile_fields.append(ProfileField.objects.get(key=field['key']))
        except Exception:
            continue
    return profile_fields

def resolve_site(*_):
    return get_site()


def resolve_site_settings(_, info):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.is_admin:
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    return get_site_settings()

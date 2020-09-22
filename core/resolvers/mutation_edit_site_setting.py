from graphql import GraphQLError
from core import config
from core.models import Setting, ProfileField
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN
from core.lib import remove_none_from_dict, access_id_to_acl
from core.resolvers.query_site import get_site_settings
from django.db import connection
from django.core.cache import cache
from file.models import FileFolder


def save_setting(key, value):
    # pylint: disable=unused-variable
    setting, created = Setting.objects.get_or_create(key=key)
    setting.value = value
    setting.save()
    cache.set("%s%s" % (connection.schema_name, key), value)


def get_menu_children(menu, item_id, depth=0):
    if depth == 3:
        return []
    depth = depth + 1

    children = []
    for item in menu:
        if item["parentId"] == item_id:
            children.append({"title": item["title"], "link": item["link"], "children": get_menu_children(menu, item["id"], depth)})
    return children


def resolve_edit_site_setting(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.is_admin:
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    setting_keys = {
        'language': 'LANGUAGE',
        'name': 'NAME',
        'description': 'DESCRIPTION',
        'isClosed': 'IS_CLOSED',
        'allowRegistration': 'ALLOW_REGISTRATION',
        'defaultAccessId': 'DEFAULT_ACCESS_ID',
        'googleAnalyticsUrl': 'GOOGLE_ANALYTICS_URL',
        'googleSiteVerification': 'GOOGLE_SITE_VERIFICATION',
        'piwikUrl': 'PIWIK_URL',
        'piwikId': 'PIWIK_ID',

        'theme': 'THEME',
        'logoAlt': 'LOGO_ALT',
        'likeIcon': 'LIKE_ICON',
        'font': 'FONT',
        'colorPrimary': 'COLOR_PRIMARY',
        'colorSecondary': 'COLOR_SECONDARY',
        'colorHeader': 'COLOR_HEADER',

        'startPage': 'STARTPAGE',
        'startPageCms': 'STARTPAGE_CMS',
        'showIcon': 'ICON_ENABLED',

        "numberOfFeaturedItems": 'NUMBER_OF_FEATURED_ITEMS',
        "enableFeedSorting": 'ENABLE_FEED_SORTING',
        'showExtraHomepageFilters': 'ACTIVITY_FEED_FILTERS_ENABLED',
        'showLeader': 'LEADER_ENABLED',
        'showLeaderButtons': 'LEADER_BUTTONS_ENABLED',
        'leaderImage': 'LEADER_IMAGE',
        'subtitle': 'SUBTITLE',
        'showInitiative': 'INITIATIVE_ENABLED',
        'initiativeTitle': 'INITIATIVE_TITLE',
        'initiativeDescription': 'INITIATIVE_DESCRIPTION',
        'initiativeImage': 'INITIATIVE_IMAGE',
        'initiativeImageAlt': 'INITIATIVE_IMAGE_ALT',
        'initiativeLink': 'INITIATIVE_LINK',
        'directLinks': 'DIRECT_LINKS',
        'footer': 'FOOTER',

        'profileSections': 'PROFILE_SECTIONS',

        'tagCategories': 'TAG_CATEGORIES',
        'showTagsInFeed': 'SHOW_TAGS_IN_FEED',
        'showTagsInDetail': 'SHOW_TAGS_IN_DETAIL',

        'defaultEmailOverviewFrequency': 'EMAIL_OVERVIEW_DEFAULT_FREQUENCY',
        'emailOverviewSubject': 'EMAIL_OVERVIEW_SUBJECT',
        'emailOverviewTitle': 'EMAIL_OVERVIEW_TITLE',
        'emailOverviewIntro': 'EMAIL_OVERVIEW_INTRO',
        'emailOverviewEnableFeatured': 'EMAIL_OVERVIEW_ENABLE_FEATURED',
        'emailOverviewFeaturedTitle': 'EMAIL_OVERVIEW_FEATURED_TITLE',
        'emailNotificationShowExcerpt': 'EMAIL_NOTIFICATION_SHOW_EXCERPT',

        'showLoginRegister': 'SHOW_LOGIN_REGISTER',
        'customTagsAllowed': 'CUSTOM_TAGS_ENABLED',
        'showUpDownVoting': 'SHOW_UP_DOWN_VOTING',
        'enableSharing': 'ENABLE_SHARING',
        'showViewsCount': 'SHOW_VIEW_COUNT',
        'newsletter': 'NEWSLETTER',
        'cancelMembershipEnabled': 'CANCEL_MEMBERSHIP_ENABLED',
        'advancedPermissions': 'ADVANCED_PERMISSIONS_ENABLED',
        'showExcerptInNewsCard': 'SHOW_EXCERPT_IN_NEWS_CARD',
        'commentsOnNews': 'COMMENT_ON_NEWS',
        'eventExport': 'EVENT_EXPORT',
        'questionerCanChooseBestAnswer': 'QUESTIONER_CAN_CHOOSE_BEST_ANSWER',
        'statusUpdateGroups': 'STATUS_UPDATE_GROUPS',
        'subgroups': 'SUBGROUPS',
        'groupMemberExport': 'GROUP_MEMBER_EXPORT',
        'limitedGroupAdd': 'LIMITED_GROUP_ADD',

        'onboardingEnabled': 'ONBOARDING_ENABLED',
        'onboardingForceExistingUsers': 'ONBOARDING_FORCE_EXISTING_USERS',
        'onboardingIntro': 'ONBOARDING_INTRO',

        'cookieConsent': 'COOKIE_CONSENT'

    }

    for k, v in setting_keys.items():
        if k in clean_input:
            save_setting(v, clean_input.get(k))

    if 'menu' in clean_input:
        menu = []
        for item in clean_input.get('menu'):
            if item['parentId'] is None:
                menu.append({"title": item["title"], "link": item["link"], "children": get_menu_children(clean_input.get('menu'), item["id"])})
        save_setting('MENU', menu)

    if 'profile' in clean_input:
        for field in clean_input.get('profile'):
            profile_field, created = ProfileField.objects.get_or_create(key=field['key'])
            profile_field.name = field['name']
            profile_field.is_filter = field['isFilter']
            profile_field.is_in_overview = field['isInOverview']
            profile_field.save()

        save_setting('PROFILE', clean_input.get('profile'))

    if 'logo' in clean_input:
        if not clean_input.get("logo"):
            raise GraphQLError("NO_FILE")

        # TODO: upload to a logo folder?
        logo = FileFolder()

        logo.owner = user
        logo.upload = clean_input.get("logo")

        logo.read_access = access_id_to_acl(logo, 2)
        logo.write_access = access_id_to_acl(logo, 0)

        logo.save()

        save_setting('LOGO', logo.embed_url)

    if 'removeLogo' in clean_input:
        try:
            FileFolder.objects.get(id=config.LOGO.split('/')[3]).delete()
        except Exception:
            pass
        save_setting('LOGO', "")

    if 'icon' in clean_input:
        if not clean_input.get("icon"):
            raise GraphQLError("NO_FILE")

        # TODO: upload to an icon folder?
        icon = FileFolder()

        icon.owner = user
        icon.upload = clean_input.get("icon")

        icon.read_access = access_id_to_acl(icon, 2)
        icon.write_access = access_id_to_acl(icon, 0)

        icon.save()

        save_setting('ICON', icon.embed_url)

    if 'removeIcon' in clean_input:
        try:
            FileFolder.objects.get(id=config.ICON.split('/')[3]).delete()
        except Exception:
            pass
        save_setting('ICON', "")

    return {
        "siteSettings": get_site_settings()
    }

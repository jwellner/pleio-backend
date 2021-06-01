import datetime
import ipaddress
from graphql import GraphQLError
from core import config
from core.models import Setting, ProfileField
from core.models.user import validate_profile_sections
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_VALUE, REDIRECTS_HAS_LOOP, REDIRECTS_HAS_DUPLICATE_SOURCE
from core.lib import remove_none_from_dict, access_id_to_acl, is_valid_domain, is_valid_url_or_path, get_language_options
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


def validate_redirects(redirects):
    sources = []
    destinations = []
    redirects_dict = {}

    # check no more than 2000 redirects
    if len(redirects) > 2000:
        raise GraphQLError(INVALID_VALUE)

    for redirect in redirects:
        source = redirect['source']
        destination = redirect['destination']
        sources.append(source)
        destinations.append(destination)
        if not is_valid_url_or_path(source) or not is_valid_url_or_path(destination):
            raise GraphQLError(INVALID_VALUE)

        # save redirects as dict, because source can not be duplicate
        try:
            redirects_dict[source] = destination
        except Exception:
            raise GraphQLError(REDIRECTS_HAS_DUPLICATE_SOURCE)

    # check if loop can occur
    if any(x in sources for x in destinations):
        raise GraphQLError(REDIRECTS_HAS_LOOP)
    return redirects_dict

def resolve_edit_site_setting(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    setting_keys = {
        'language': 'LANGUAGE',
        'name': 'NAME',
        'description': 'DESCRIPTION',
        'isClosed': 'IS_CLOSED',
        'allowRegistration': 'ALLOW_REGISTRATION',
        'defaultAccessId': 'DEFAULT_ACCESS_ID',
        'googleAnalyticsId': 'GOOGLE_ANALYTICS_ID',
        'googleSiteVerification': 'GOOGLE_SITE_VERIFICATION',
        'enableSearchEngineIndexing': 'ENABLE_SEARCH_ENGINE_INDEXING',
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
        'iconAlt': 'ICON_ALT',

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
        'showExcerptInNewsCard': 'SHOW_EXCERPT_IN_NEWS_CARD',
        'commentsOnNews': 'COMMENT_ON_NEWS',
        'eventExport': 'EVENT_EXPORT',
        'eventTiles': 'EVENT_TILES',
        'questionerCanChooseBestAnswer': 'QUESTIONER_CAN_CHOOSE_BEST_ANSWER',
        'statusUpdateGroups': 'STATUS_UPDATE_GROUPS',
        'subgroups': 'SUBGROUPS',
        'groupMemberExport': 'GROUP_MEMBER_EXPORT',
        'limitedGroupAdd': 'LIMITED_GROUP_ADD',

        'onboardingEnabled': 'ONBOARDING_ENABLED',
        'onboardingForceExistingUsers': 'ONBOARDING_FORCE_EXISTING_USERS',
        'onboardingIntro': 'ONBOARDING_INTRO',

        'profileSyncEnabled': 'PROFILE_SYNC_ENABLED',
        'profileSyncToken': 'PROFILE_SYNC_TOKEN',

        'cookieConsent': 'COOKIE_CONSENT',
        'loginIntro': 'LOGIN_INTRO',
        'siteMembershipAcceptedIntro': 'SITE_MEMBERSHIP_ACCEPTED_INTRO',
        'siteMembershipDeniedIntro': 'SITE_MEMBERSHIP_DENIED_INTRO',
        'idpId': 'IDP_ID',
        'idpName': 'IDP_NAME',

        'flowEnabled': 'FLOW_ENABLED',
        'flowSubtypes': 'FLOW_SUBTYPES',
        'flowAppUrl': 'FLOW_APP_URL',
        'flowToken': 'FLOW_TOKEN',
        'flowCaseId': 'FLOW_CASE_ID',
        'flowUserGuid': 'FLOW_USER_GUID'
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

    if 'redirects' in clean_input:
        redirects = validate_redirects(clean_input.get('redirects'))
        save_setting('REDIRECTS', redirects)

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

    if 'directRegistrationDomains' in clean_input:
        for domain in clean_input.get('directRegistrationDomains'):
            if not is_valid_domain(domain):
                raise GraphQLError(INVALID_VALUE)
        save_setting('DIRECT_REGISTRATION_DOMAINS', clean_input.get('directRegistrationDomains'))

    if 'profileSections' in clean_input:
        save_setting('PROFILE_SECTIONS', validate_profile_sections(clean_input.get('profileSections')))

    if 'customCss' in clean_input:
        save_setting('CUSTOM_CSS', clean_input.get('customCss'))
        save_setting('CUSTOM_CSS_TIMESTAMP', int(datetime.datetime.now().timestamp()))

    if 'walledGardenByIpEnabled' in clean_input:
        save_setting('WALLED_GARDEN_BY_IP_ENABLED', clean_input.get('walledGardenByIpEnabled'))

        # if walled garden by ip is enabled, turn of indexing
        if clean_input.get('walledGardenByIpEnabled'):
            save_setting('ENABLE_SEARCH_ENGINE_INDEXING', False)

    if 'whitelistedIpRanges' in clean_input:
        for ip_range in clean_input.get('whitelistedIpRanges'):
            try:
                ip_addr = ipaddress.ip_network(ip_range)
            except ValueError:
                raise GraphQLError(INVALID_VALUE)
        save_setting('WHITELISTED_IP_RANGES', clean_input.get('whitelistedIpRanges'))

    if 'extraLanguages' in clean_input:
        options = set((i['value'] for i in get_language_options()))
        for language in clean_input.get('extraLanguages'):
            if language not in options:
                raise GraphQLError(INVALID_VALUE)
        save_setting('EXTRA_LANGUAGES', clean_input.get('extraLanguages'))

    return {
        "siteSettings": get_site_settings()
    }

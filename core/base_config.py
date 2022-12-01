from django.db import connection
from django.core.cache import cache
from django.apps import apps

DEFAULT_SITE_CONFIG = {
    'BACKEND_VERSION': ('2.0', 'Backend version'),
    'NAME': ('Pleio 2.0', 'Name'),
    'DESCRIPTION': ('Omschrijving site', 'Description'),
    'LANGUAGE': ('nl', 'Language'),
    'EXTRA_LANGUAGES': ([], 'Extra languages'),
    'IS_CLOSED': (True, 'Is site closed'),
    'ALLOW_REGISTRATION': (True, 'Allow registrations'),
    'DIRECT_REGISTRATION_DOMAINS': ([], 'Direct registration domains'),
    'DEFAULT_ACCESS_ID': (1, 'Default accessId'),
    'GOOGLE_ANALYTICS_ID': ('', 'Google analytics ID'),
    'GOOGLE_SITE_VERIFICATION': ('', 'Google site verification code'),
    'PIWIK_URL': ('https://stats.pleio.nl/', 'Piwik url'),
    'PIWIK_ID': ('', 'Piwik ID'),
    'OIDC_PROVIDERS': (['pleio'], 'OIDC Providers'),
    'REQUIRE_2FA': (False, 'Allow/forbid users without 2fa'),
    'FILE_OPTIONS': ([], "File options"),
    'AUTO_APPROVE_SSO': (False, 'Automatically approve users that use one of configured SSO options'),
    'CUSTOM_JAVASCRIPT': ('', 'Custom Javascript'),

    'THEME_OPTIONS': (
        [{"value": 'leraar', 'label': 'Standaard'}, {'value': 'rijkshuisstijl', 'label': 'Rijkshuisstijl'}],
        'Default theme options'
    ),

    'FONT': ('Rijksoverheid Sans', 'Font'),
    'COLOR_PRIMARY': ('#0e2f56', 'Primary color'),
    'COLOR_SECONDARY': ('#009ee3', 'Secondary color'),
    'COLOR_HEADER': ('', 'Header color'),

    'THEME': ('leraar', 'Theme'),
    'LOGO': ('', 'Logo'),
    'LOGO_ALT': ('', 'Logo alt text'),
    'FAVICON': ('', 'Favicon'),
    'FAVICON_16': ('', 'Favicon 16x16'),
    'FAVICON_32': ('', 'Favicon 32x32'),
    'LIKE_ICON': ('heart', 'Like icon'),

    'ICON': ('', 'Icon'),
    'ICON_ALT': ('', 'Icon alt text'),
    'ICON_ENABLED': (False, 'Icon enabled'),

    'STARTPAGE': ('activity', 'Startpage'),
    'STARTPAGE_CMS': ('', 'Startpage cms'),
    'ANONYMOUS_START_PAGE': ('', 'Start page type for anonymous visitors'),
    'ANONYMOUS_START_PAGE_CMS': ('', 'Start page CMS page guid for anonymous visitors'),

    'NUMBER_OF_FEATURED_ITEMS': (0, 'Number of featured items'),
    'ENABLE_FEED_SORTING': (False, 'Enable feed sorting'),
    'ACTIVITY_FEED_FILTERS_ENABLED': (True, 'Activity filters enabled'),
    'SUBTITLE': ('', 'Subtitle'),
    'LEADER_ENABLED': (False, 'Leader enabled'),
    'LEADER_BUTTONS_ENABLED': (False, 'Leader buttons enabled'),
    'LEADER_IMAGE': ('', 'Leader image'),
    'INITIATIVE_ENABLED': (False, 'Initiative enabled'),
    'INITIATIVE_TITLE': ('', 'Initiative title'),
    'INITIATIVE_IMAGE': ('', 'Initiavite image'),
    'INITIATIVE_IMAGE_ALT': ('', 'Initiative image alt text'),
    'INITIATIVE_DESCRIPTION': ('', 'Initiative description'),
    'INITIATIVE_LINK': ('', 'Initiative link'),
    'DIRECT_LINKS': ([], 'Direct links'),
    'FOOTER': ([], 'Footer'),
    'REDIRECTS': ({}, 'Redirects'),

    'MENU': ([
                 {"link": "/blog", "title": "Blog", "children": [], "accessId": 2},
                 {"link": "/news", "title": "Nieuws", "children": [], "accessId": 2},
                 {"link": "/groups", "title": "Groepen", "children": [], "accessId": 2},
                 {"link": "/questions", "title": "Vragen", "children": [], "accessId": 2},
                 {"link": "/wiki", "title": "Wiki", "children": [], "accessId": 2}
             ], 'Menu'),
    'MENU_STATE': ('normal', "Menu state"),

    'PROFILE': ([], 'Profile'),
    'PROFILE_SECTIONS': ([], 'Profile sections'),

    'TAG_CATEGORIES': ([], 'Tag categories'),
    'SHOW_TAGS_IN_FEED': (False, 'Show tags in feed'),
    'SHOW_TAGS_IN_DETAIL': (False, 'Show tags in detail'),

    'EMAIL_OVERVIEW_DEFAULT_FREQUENCY': ("weekly", 'Email overview default frequency'),
    'EMAIL_OVERVIEW_SUBJECT': ("", "Email overview subject"),
    'EMAIL_OVERVIEW_TITLE': ("Pleio 2.0", "Email overview title"),
    'EMAIL_OVERVIEW_INTRO': ("", "Email overview intro"),
    'EMAIL_OVERVIEW_ENABLE_FEATURED': (False, 'Show featured items in overview email'),
    'EMAIL_OVERVIEW_FEATURED_TITLE': ("", "Email overview featured title"),
    'EMAIL_NOTIFICATION_SHOW_EXCERPT': (False, 'Show excerpts in notification email'),

    'SHOW_LOGIN_REGISTER': (True, 'Login and register buttons visible'),
    'CUSTOM_TAGS_ENABLED': (True, 'Custom tags enabled'),
    'SHOW_UP_DOWN_VOTING': (True, 'Show up and down voting'),
    'ENABLE_SHARING': (True, 'Enable sharing'),
    'SHOW_VIEW_COUNT': (True, 'Show view count'),
    'NEWSLETTER': (False, 'Newsletter'),
    'CANCEL_MEMBERSHIP_ENABLED': (True, 'Cancel membership enabled'),
    'SHOW_EXCERPT_IN_NEWS_CARD': (False, 'Show excerpt in news card'),
    'COMMENT_ON_NEWS': (False, 'Comment on news'),
    'EVENT_EXPORT': (False, 'Event Export'),
    'EVENT_TILES': (False, 'Event Tiles'),
    'QUESTIONER_CAN_CHOOSE_BEST_ANSWER': (False, 'Questioner can choose best answer'),
    'STATUS_UPDATE_GROUPS': (True, 'Status update groups'),
    'SUBGROUPS': (False, 'Subgroups'),
    'GROUP_MEMBER_EXPORT': (False, 'Group member export'),
    'LIMITED_GROUP_ADD': (True, 'Adding of groups limited to admins'),
    'SHOW_SUGGESTED_ITEMS': (False, 'Show suggested items'),

    'ACHIEVEMENTS_ENABLED': (True, 'Achievements enabled'),
    'MAIL_REPLY_TO': ('noreply@pleio.nl', 'default reply-to mail address'),
    'ENABLE_SEARCH_ENGINE_INDEXING': (False, 'Enable indexing by search engines'),

    'ONBOARDING_ENABLED': (False, 'Onboarding enabled'),
    'ONBOARDING_FORCE_EXISTING_USERS': (False, 'Onboarding force existing users'),
    'ONBOARDING_INTRO': ("", 'Onboarding intro'),

    'COOKIE_CONSENT': (False, 'Cookie consent enabled'),
    'LOGIN_INTRO': ('', 'Login intro text'),

    'PROFILE_SYNC_ENABLED': (False, 'Profile sync api enabled'),
    'PROFILE_SYNC_TOKEN': ("", 'Profile sync api token'),

    'TENANT_API_TOKEN': (None, "Tenant API token"),

    'CUSTOM_CSS': ("", 'Custom Css'),
    'CUSTOM_CSS_TIMESTAMP': ("", 'Custom Css timestamp'),
    'WHITELISTED_IP_RANGES': ([], 'Whitelisted ip ranges'),
    'WALLED_GARDEN_BY_IP_ENABLED': (False, 'Walled garden by ip enabled'),
    'SITE_MEMBERSHIP_ACCEPTED_INTRO': ("", 'Site membership accepted intro'),
    'SITE_MEMBERSHIP_DENIED_INTRO': ("", 'Site membership denied intro'),
    'IDP_ID': ("", 'Identity provider ID'),
    'IDP_NAME': ("", 'Identity provider name'),
    'FLOW_ENABLED': (False, 'Flow enabled'),
    'FLOW_SUBTYPES': ([], 'Flow subtypes'),
    'FLOW_APP_URL': ("", 'Flow app url'),
    'FLOW_TOKEN': ("", 'Flow token'),
    'FLOW_CASE_ID': (None, 'Flow case id'),
    'FLOW_USER_GUID': ("", 'Flow user guid'),
    'EDIT_USER_NAME_ENABLED': (False, 'Allow users to change name'),
    'COMMENT_WITHOUT_ACCOUNT_ENABLED': (False, 'Allow anonymous users to comment'),
    'QUESTION_LOCK_AFTER_ACTIVITY': (False, 'Lock questions after comments are given'),
    'QUESTION_LOCK_AFTER_ACTIVITY_LINK': ("", 'Link for locked questions'),

    'LAST_RECEIVED_BOUNCING_EMAIL': ("2021-01-01", 'Last received bouncing email'),
    'LAST_RECEIVED_DELETED_USER': ("2021-01-01", 'Last received deleted user'),
    'CSP_HEADER_EXCEPTIONS': ([], 'CSP header exceptions'),

    'KALTURA_VIDEO_ENABLED': (False, 'Allow adding Kaltura videos'),
    'KALTURA_VIDEO_PARTNER_ID': ('', 'Partner ID for Kaltura video urls'),
    'KALTURA_VIDEO_PLAYER_ID': ('', 'Player ID for Kaltura video urls'),

    'PDF_CHECKER_ENABLED': (True, 'PDFChecker enabled'),

    'MAX_CHARACTERS_IN_ABSTRACT': (320, 'Maximum characters in abstract'),
    'COLLAB_EDITING_ENABLED': (False, 'Is collaborative editing enabled'),

    'PRESERVE_FILE_EXIF': (False, 'Preserve the EXIF data of uploaded files'),

    'ONLINEAFSPRAKEN_ENABLED': (None, "Onlineafspraken.nl enabled switch"),
    'ONLINEAFSPRAKEN_KEY': (None, "Onlineafspraken.nl api key"),
    'ONLINEAFSPRAKEN_SECRET': (None, "Onlineafspraken.nl api secret"),
    'ONLINEAFSPRAKEN_URL': (None, "Override onlineafspraken.nl api url"),
    'VIDEOCALL_ENABLED': (None, "Enable videocall api"),
    'VIDEOCALL_API_URL': (None, "Override videocall api url"),
    'VIDEOCALL_PROFILEPAGE': (None, "Allow initiate videocall from profile page"),
    'VIDEOCALL_THROTTLE': (10, "Maximum number of room reservations per hour"),
    'VIDEOCALL_APPOINTMENT_TYPE': ([], "Setup what appointment-types trigger create a videocall link"),

    'SUPPORT_CONTRACT_ENABLED': (False, "Support contract enabled for site"),
    'SUPPORT_CONTRACT_HOURS_REMAINING': (0, "Support contract hours remaining for site"),
    'SEARCH_ARCHIVE_OPTION': ('nobody', "Allow filter archived articles on search"),
    'BLOCKED_USER_INTRO_MESSAGE': ('', "Custom message to show blocked users at login attempts.")
}
"""
Default site configuration

Valid JSONFields types:
- boolean
- string
- integer
- float
- dict
- list
"""


class ConfigBackend():
    def __init__(self):
        self._model = apps.get_model('core.Setting')
        self.init()

    def get(self, key):
        value = cache.get("%s%s" % (connection.schema_name, key))

        if value is None:
            try:
                value = self._model.objects.get(key=key).value
            except self._model.DoesNotExist:
                pass
            else:
                cache.set("%s%s" % (connection.schema_name, key), value)

        return value

    def set(self, key, value):
        setting, created = self._model.objects.get_or_create(key=key)
        if created or setting.value != value:
            setting.value = value
            setting.save()

        cache.set("%s%s" % (connection.schema_name, key), value)

    def init(self):
        # fill cache on init
        if not connection.schema_name == 'public':
            for setting in self._model.objects.all():
                if setting.key in DEFAULT_SITE_CONFIG:
                    cache.set("%s%s" % (connection.schema_name, setting.key), setting.value)


class Config():
    def __init__(self):
        super(Config, self).__setattr__('_backend', ConfigBackend())

    def __getattr__(self, key):
        try:
            if not len(DEFAULT_SITE_CONFIG[key]) in (2, 3):
                raise AttributeError(key)
            default = DEFAULT_SITE_CONFIG[key][0]
        except KeyError:
            raise AttributeError(key)
        result = self._backend.get(key)

        if result is None:
            result = default
            setattr(self, key, default)
            return result
        return result

    def __setattr__(self, key, value):
        if key not in DEFAULT_SITE_CONFIG:
            raise AttributeError(key)
        self._backend.set(key, value)

    def __dir__(self):
        return DEFAULT_SITE_CONFIG.keys()

    def reset(self):
        self._backend.init()

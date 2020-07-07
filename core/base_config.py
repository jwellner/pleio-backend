from django.db import OperationalError, ProgrammingError
from django.db import connection
from django.core.cache import cache
from django.apps import apps

DEFAULT_SITE_CONFIG = {
    'BACKEND_VERSION': ('2.0', 'Backend version'),
    'NAME': ('Pleio 2.0', 'Name'),
    'DESCRIPTION': ('Omschrijving site', 'Description'),
    'LANGUAGE': ('nl', 'Language'),
    'IS_CLOSED': (False, 'Is site closed'),
    'ALLOW_REGISTRATION': (True, 'Allow registrations'),
    'DEFAULT_ACCESS_ID': (1, 'Default accessId'),

    'GOOGLE_ANALYTICS_URL': ('', 'Google analytics url'),
    'GOOGLE_SITE_VERIFICATION': ('', 'Google site verification code'),
    'PIWIK_URL': ('', 'Piwik url'),
    'PIWIK_ID': ('', 'Piwik id'),

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
    'LIKE_ICON': ('heart', 'Like icon'),

    'ICON': ('', 'Icon'),
    'ICON_ALT': ('', 'Icon alt text'),
    'ICON_ENABLED': (False, 'Icon enabled'),
    'STARTPAGE': ('activity', 'Startpage'),

    'STARTPAGE_CMS': ('', 'Startpage cms'),

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

    'MENU': ([
        {"link": "/blog", "title": "Blog", "children": []},
        {"link": "/news", "title": "Nieuws", "children": []},
        {"link": "/groups", "title": "Groepen", "children": []},
        {"link": "/questions", "title": "Vragen", "children": []},
        {"link": "/wiki", "title": "Wiki", "children": []}
    ], 'Menu'),

    'PROFILE': ([], 'Profile'),

    'TAG_CATEGORIES': ([], 'Tag categories'),
    'SHOW_TAGS_IN_FEED': (False, 'Show tags in feed'),
    'SHOW_TAGS_IN_DETAIL': (False, 'Show tags in detail'),

    'EMAIL_OVERVIEW_DEFAULT_FREQUENCY':  ("weekly", 'Email overview default frequency'),
    'EMAIL_OVERVIEW_SUBJECT': ("", "Email overview subject"),
    'EMAIL_OVERVIEW_TITLE': ("Pleio 2.0", "Email overview title"),
    'EMAIL_OVERVIEW_INTRO': ("", "Email overview intro"),

    'SHOW_LOGIN_REGISTER': (True, 'Login and register buttons visible'),
    'CUSTOM_TAGS_ENABLED': (True, 'Custom tags enabled'),
    'SHOW_UP_DOWN_VOTING': (True, 'Show up and down voting'),
    'ENABLE_SHARING': (True, 'Enable sharing'),
    'SHOW_VIEW_COUNT': (True, 'Show view count'),
    'NEWSLETTER': (False, 'Newsletter'),
    'CANCEL_MEMBERSHIP_ENABLED': (True, 'Cancel membership enabled'),
    'ADVANCED_PERMISSIONS_ENABLED': (False, 'Advanced permissions'),
    'SHOW_EXCERPT_IN_NEWS_CARD': (False, 'Show excerpt in news card'),
    'COMMENT_ON_NEWS': (False, 'Comment on news'),
    'EVENT_EXPORT': (False, 'Event Export'),
    'QUESTIONER_CAN_CHOOSE_BEST_ANSWER': (False, 'Questioner can choose best answer'),
    'STATUS_UPDATE_GROUPS': (True, 'Status update groups'),
    'SUBGROUPS': (False, 'Subgroups'),
    'GROUP_MEMBER_EXPORT': (False, 'Group member export'),
    'LIMITED_GROUP_ADD': (True, 'Adding of groups limited to admins'),


    'ACHIEVEMENTS_ENABLED': (True, 'Achievements enabled'),
    'INITIATOR_LINK': ('', 'Initiator link'),
    'MAIL_REPLY_TO': ('noreply@pleio.nl', 'default reply-to mail address'),
    'ENABLE_SEARCH_ENGINE_INDEXING': (False, 'Enable indexing by search engines'),
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

    def get(self, key):
        value = cache.get("%s%s" % (connection.schema_name, key))

        if value is None:
            try:
                value = self._model.objects.get(key=key).value
            except (OperationalError, ProgrammingError, self._model.DoesNotExist):
                pass
            else:
                cache.set("%s%s" % (connection.schema_name, key), value)

        return value

    def set(self, key, value):
        try:
            setting = self._model.objects.get(key=key)
        except (OperationalError, ProgrammingError):
            return
        except self._model.DoesNotExist:
            setting = self._model.objects.create(key=key, value=value)
        else:
            setting.value = value
            setting.save()

        cache.set("%s%s" % (connection.schema_name, key), value)


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

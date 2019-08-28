from django.db import OperationalError, ProgrammingError
from django.core.cache import cache

DEFAULT_SITE_CONFIG = {
    'NAME': ('Pleio 2.0', 'Name'),
    'SUBTITLE': ('', 'Subtitle'),
    'THEME': ('', 'Theme'),
    'ACHIEVEMENTS_ENABLED': (True, 'Achievements enabled'),
    'CANCEL_MEMBERSHIP_ENABLED': (True, 'Cancel membership enabled'),
    'DEFAULT_ACCESS_ID': (1, 'Default accessId'),
    'LOGO': ('', 'Logo'),
    'LOGO_ALT': ('', 'Logo alt text'),
    'ICON': ('', 'Icon'),
    'ICON_ALT': ('', 'Icon alt text'),
    'ICON_ENABLED': (False, 'Icon enabled'),
    'STARTPAGE': ('activity', 'Startpage'),
    'LEADER_ENABLED': (False, 'Leader enabled'),
    'LEADER_BUTTONS_ENABLED': (False, 'Leader buttons enabled'),
    'LEADER_IMAGE': ('', 'Leader image'),
    'INITIATIVE_ENABLED': (False, 'Initiative enabled'),
    'INITIATIVE_TITLE': ('', 'Initiative title'),
    'INITIATIVE_IMAGE': ('', 'Initiavite image'),
    'INITIATIVE_IMAGE_ALT': ('', 'Initiative image alt text'),
    'INITIATIVE_DESCRIPTION': ('', 'Initiative description'),
    'INITIATOR_LINK': ('', 'Initiator link'),
    'STYLE': ({
        'font': 'Arial',
        'colorPrimary': '#0e2f56',
        'colorSecondary': '#118df0',
        'colorHeader': 'red'
    }, 'Style'),
    'CUSTOM_TAGS_ENABLED': (True, 'Custom tags enabled'),
    'TAG_CATEGORIES': ([], 'Tag categories'),
    'ACTIVITY_FEED_FILTERS_ENABLED': (True, 'Activity filters enabled'),
    'MENU': ([], 'Menu'),
    'FOOTER': ([], 'Footer'),
    'DIRECT_LINKS': ([], 'Direct links')
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
        from core.models import Setting
        self._model = Setting
        self._cache_prefix = ""

    def cache_prefix(self, key):
        return "%s%s" % (self._cache_prefix, key)

    def get(self, key):

        value = cache.get(self.cache_prefix(key))

        if value is None:
            try:
                value = self._model.objects.get(key=key).value
            except (OperationalError, ProgrammingError, self._model.DoesNotExist):
                pass
            else:
                cache.set(self.cache_prefix(key), value)
        
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

        cache.set(self.cache_prefix(key), value)


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

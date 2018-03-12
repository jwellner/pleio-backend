from django.utils.translation import ugettext_lazy as _

SECRET_KEY = 'b04*myk_%9&^x5elbx(j@l_76y%g(q4q98ny2*gdc0v#b+j2h7'

DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'backend2'
    }
}

TIME_ZONE = 'Europe/Amsterdam'

FROM_EMAIL = 'Pleio <noreply@pleio.nl>'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

LOCAL_APPS = [
    #'example'
]

LOCAL_MIDDLEWARE = []

LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en-us', _('English')),
    ('nl-nl', _('Dutch')),
    ('fr-fr', _('French'))
]

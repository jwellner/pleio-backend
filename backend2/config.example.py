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

TIME_ZONE = 'UTC'

FROM_EMAIL = 'Backend <noreply@backend.com>'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

LOCAL_APPS = [
    'blog',
]

LOCAL_MIDDLEWARE = []

LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en-us', _('English')),
    ('nl-nl', _('Dutch')),
    ('fr-fr', _('French'))
]

OIDC_RP_CLIENT_ID = '12345'
OIDC_RP_CLIENT_SECRET = 'secret'
OIDC_RP_SCOPES = 'openid profile email picture'

OIDC_OP_AUTHORIZATION_ENDPOINT = 'http://localhost:8001/openid/authorize/'
OIDC_OP_TOKEN_ENDPOINT = 'http://localhost:8001/openid/token/'
OIDC_OP_USER_ENDPOINT = 'http://localhost:8001/openid/userinfo/'
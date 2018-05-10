from django.utils.translation import ugettext_lazy as _
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST')]

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('DB_HOST'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': os.getenv('DB_NAME'),
    }
}

TIME_ZONE = 'UTC'

STATIC_ROOT  = '/app/static'

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

SECRET_KEY = 'b04*myk_%9&^x5elbx(j@l_76y%g(q4q98ny2*gdc0v#b+j2h7'

DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'backend2'
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

FROM_EMAIL = 'Backend <noreply@backend.com>'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

LOCAL_APPS = [
    'example'
]

LOCAL_MIDDLEWARE = []

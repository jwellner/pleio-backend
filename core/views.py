import json
from core.resolvers.query_site import get_settings
from core import config
from django.contrib.auth.views import LogoutView, LoginView
from django.shortcuts import redirect, render
from django.conf import settings



def default(request):

    context = {
        'lang': config.LANGUAGE,
        'title': config.NAME,
        'theme': config.THEME,
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings())
    }

    return render(request, 'react.html', context)

def logout(request):
    LogoutView.as_view()(request)

    return redirect('/')

def login(request):
    return LoginView.as_view()(request)

def oidc_failure(request):
    return redirect(settings.OIDC_OP_LOGOUT_ENDPOINT)

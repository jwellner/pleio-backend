from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, LoginView
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.conf import settings
from core.models import BinaryFile
from core.lib import get_settings
import json

def default(request):

    context = {
        'lang': 'nl',
        'title': 'Pleio 3.0',
        'theme': 'leraar',
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings())
    }

    return render(request, 'react.html', context)


@login_required
def upload(request):
    if not request.method == 'POST':
        return HttpResponseBadRequest()

    uploaded_file = request.FILES['file']

    binary_file = BinaryFile.objects.create(
        owner=request.user,
        file=uploaded_file,
        name=uploaded_file.name,
        size=uploaded_file.size,
        content_type=uploaded_file.content_type
    )

    data = {
        'id': '{}.{}:{}'.format(
            binary_file._meta.app_label,
            binary_file._meta.object_name,
            binary_file.id
        ).lower()
    }

    return JsonResponse(data)


def logout(request):
    LogoutView.as_view()(request)

    return redirect('/')

def login(request):
    return LoginView.as_view()(request)

def oidc_failure(request):
    return redirect(settings.OIDC_OP_LOGOUT_ENDPOINT)

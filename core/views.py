from django.contrib.auth.views import LogoutView, LoginView
from django.shortcuts import redirect, render
from django.conf import settings
from core.lib import get_settings
import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404 
from core.models import FileFolder
from django.http import StreamingHttpResponse

def default(request):

    context = {
        'lang': 'nl',
        'title': 'Pleio 3.0',
        'theme': 'leraar',
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

def download(request, file_id=None, file_name=None):
    user = request.user

    if not file_id or not file_name:
        raise Http404("File not found")

    try:
        entity = FileFolder.objects.visible(user).get(id=file_id)
        response = StreamingHttpResponse(streaming_content=entity.upload.open(), content_type=entity.content_type)
        response['Content-Length'] = entity.upload.size
        response['Content-Disposition'] = "attachment; filename=%s" % file_name
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")

    raise Http404("File not found")

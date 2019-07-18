from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, LoginView
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from .models import BinaryFile


def index(request):
    return JsonResponse({
        'app': 'backend2',
        'status': 200,
        'description': 'Backend2 is working correctly. '
                       'Visit /graphql/ for the GraphQL API, '
                       'visit /oidc/authenticate/ for login, '
                       'visit /logout/ for logout, '
                       'visit /admin/ for the admin panel.'
    })


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
    print('oidc_failure')

    oidc_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    return redirect(oidc_url)

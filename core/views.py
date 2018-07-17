from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from .models import BinaryFile

def index(request):
    return JsonResponse({
        'app': 'backend2',
        'status': 200,
        'description': 'Backend2 is working correctly. Visit /graphql/ for the GraphQL API, visit /oidc/authenticate/ for login, visit /admin/ for the admin panel.'
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
        'id': '{}.{}:{}'.format(binary_file._meta.app_label, binary_file._meta.object_name, binary_file.id).lower()
    }

    return JsonResponse(data)
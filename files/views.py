from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from .models import BinaryFile

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
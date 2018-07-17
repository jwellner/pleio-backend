from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from .views import upload

urlpatterns = [
    path('upload/', csrf_exempt(upload), name='upload'),
]
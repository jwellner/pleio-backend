from django.urls import path
from django.contrib import admin
import core.views

urlpatterns = [
    path('', core.views.index),
    path('admin/', admin.site.urls),
]

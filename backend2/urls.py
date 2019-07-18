from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from ariadne.contrib.django.views import GraphQLView
from .schema import schema

from core import admin
from core import views

urlpatterns = [
    path('logout', views.logout, name='logout'),
    path('action/logout', views.logout, name='logout'),
    path('login', views.login, name='login'),
    path('oidc/failure/', views.oidc_failure, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('files/upload/', csrf_exempt(views.upload), name='upload'),
    path('admin/logout/', views.logout, name='logout'),
    path('admin/', admin.site.urls),
    path('graphql', GraphQLView.as_view(schema=schema), name='graphql'),
    path('', views.index, name='index')
]

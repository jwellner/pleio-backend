from django.urls import path, include, re_path

from ariadne.contrib.django.views import GraphQLView
from .schema import schema

from core import admin as core_admin
from core import views as core_views

urlpatterns = [
    path('logout', core_views.logout, name='logout'),
    path('action/logout', core_views.logout, name='logout'),
    path('login', core_views.login, name='login'),
    path('oidc/failure/', core_views.oidc_failure, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('admin/logout/', core_views.logout, name='logout'),
    path('admin/', core_admin.site.urls),
    path('graphql', GraphQLView.as_view(schema=schema), name='graphql'),
    path('file/download/<uuid:file_id>/<str:file_name>', core_views.download, name='download'),
    re_path(r'.*', core_views.default, name='default')
]

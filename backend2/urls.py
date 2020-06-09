from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.decorators.cache import cache_page

from ariadne.contrib.django.views import GraphQLView
from .schema import schema

from core.sitemaps import sitemaps
from core import admin as core_admin
from core import views as core_views
from file import views as file_views
from event import views as event_views
from elgg import views as elgg_views


urlpatterns = [
    path('logout', core_views.logout, name='logout'),
    path('action/logout', core_views.logout, name='logout'),
    path('login', core_views.login, name='login'),
    path('oidc/failure/', core_views.oidc_failure, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('admin/logout/', core_views.logout, name='logout'),
    path('admin/', core_admin.site.urls),
    path('graphql', GraphQLView.as_view(schema=schema), name='graphql'),

    path('file/download/<uuid:file_id>/<str:file_name>', file_views.download, name='download'),
    path('bulk_download', file_views.bulk_download, name='bulk_download'),
    path('file/thumbnail/<uuid:file_id>', file_views.thumbnail, name='thumbnail'),

    # TODO: make 1 url for logo and icon
    path('site/logo/<uuid:file_id>', file_views.file_cache_header, name='site_logo'),
    path('site/icon/<uuid:file_id>', file_views.file_cache_header, name='site_icon'),
    path('exporting/event/<uuid:event_id>', event_views.export, name='event_export'),

    path('robots.txt', core_views.robots_txt),
    path('sitemap.xml', cache_page(3600)(sitemap), {'sitemaps': sitemaps}, name='sitemap'),

    # Match old ID's and try to redirect
    re_path(r'view\/(?P<entity_id>[0-9]+)\/(?:.+)$', elgg_views.entity_redirect, name='entity_redirect'),

    # Default catch all URL's
    re_path(r'view\/(?P<entity_id>[0-9A-Fa-f-]+)\/(?P<entity_title>[\w\-_]+)$', core_views.entity_view, name='entity_view'),
    re_path(r'.*', core_views.default, name='default')
]

handler404 = 'core.views.default'
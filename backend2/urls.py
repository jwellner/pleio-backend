from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.decorators.cache import cache_page
from django.shortcuts import render

from ariadne.contrib.django.views import GraphQLView
from ariadne.contrib.tracing.opentracing import OpenTracingExtensionSync
from .schema import schema

from core.sitemaps import sitemaps
from core import superadmin_views as core_superadmin
from core import views as core_views
from file import views as file_views
from event import views as event_views
from user import views as user_views


urlpatterns = [
    path('logout', core_views.logout, name='logout'),
    path('action/logout', core_views.logout, name='logout'),
    path('login', core_views.login, name='login'),
    path('login/request', core_views.request_access, name='request_access'),
    path('login/requested', core_views.access_requested, name='access_requested'),
    path('oidc/failure/', core_views.logout, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('superadmin', core_superadmin.Dashboard.as_view()),
    path('superadmin/', core_superadmin.Dashboard.as_view()),
    path('superadmin/settings', core_superadmin.Settings.as_view()),
    path('superadmin/tasks', core_superadmin.tasks),
    path('superadmin/scanlog', core_superadmin.ScanLog.as_view()),
    path('graphql', GraphQLView.as_view(schema=schema, extensions=[OpenTracingExtensionSync]), name='graphql'),

    path('file/download/<uuid:file_id>', file_views.download, name='download'),
    path('file/download/<uuid:file_id>/<str:file_name>', file_views.download, name='download'),

    path('file/embed/<uuid:file_id>', file_views.embed, name='embed'),
    path('file/embed/<uuid:file_id>/<str:file_name>', file_views.embed, name='embed'),

    path('file/thumbnail/<uuid:file_id>', file_views.thumbnail, name='thumbnail'),
    path('file/featured/<uuid:entity_guid>', file_views.featured, name='featured'),

    path('attachment/<str:attachment_type>/<uuid:attachment_id>', core_views.attachment, name='attachment'),

    path('bulk_download', file_views.bulk_download, name='bulk_download'),

    path('exporting/content/<str:content_type>', core_views.export_content, name='content_export'),
    path('exporting/group/<uuid:group_id>', core_views.export_group_members, name='group_members_export'),
    path('exporting/event/<uuid:event_id>', event_views.export, name='event_export'),
    path('exporting/calendar/', event_views.export_calendar, name='event_calendar_export'),
    path('exporting/users', user_views.export, name='users_export'),

    path('comment/confirm/<uuid:entity_id>', core_views.comment_confirm, name='comment_confirm'),

    path('onboarding', core_views.onboarding, name='onboarding'),

    path('custom.css', core_views.custom_css),
    path('favicon.png', core_views.favicon),
    path('robots.txt', core_views.robots_txt),
    path('sitemap.xml', cache_page(3600)(sitemap), {'sitemaps': sitemaps}, name='sitemap'),

    path('flow/', include('flow.urls')),
    path('profile_sync_api/', include('profile_sync.urls')),

    # Include elgg url's for redirects
    path('', include('elgg.urls')),

    # Default catch all URL's
    re_path(r'view\/(?P<entity_id>[0-9A-Fa-f-]+)\/(?:[^\/.]+)$', core_views.entity_view, name='entity_view'),
    re_path(r'.*', core_views.default, name='default')
]

handler404 = 'core.views.default'

def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response

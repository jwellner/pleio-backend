from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.decorators.cache import cache_page
from django.shortcuts import render

from ariadne_django.views import GraphQLView
from ariadne.contrib.tracing.opentracing import OpenTracingExtensionSync
from .schema import schema

from core.sitemaps import sitemaps
from core import superadmin_views as core_superadmin
from core import views as core_views
from file import views as file_views
from event import views as event_views
from user import views as user_views
from concierge import views as concierge_views
from tenants import views as tenants_views

urlpatterns = [
    path('unsubscribe/<str:token>', core_views.unsubscribe, name='unsubscribe'),
    path('logout', core_views.logout, name='logout'),
    path('action/logout', core_views.logout),
    path('register', core_views.register, name='register'),
    path('login', core_views.login, name='login'),
    path('login/request', core_views.request_access, name='request_access'),
    path('login/requested', core_views.access_requested, name='access_requested'),
    path('oidc/failure/', core_views.logout, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('superadmin', core_superadmin.Dashboard.as_view()),
    path('superadmin/', core_superadmin.Dashboard.as_view()),
    path('superadmin/settings', core_superadmin.Settings.as_view()),
    path('superadmin/tasks', core_superadmin.HandleViewTasksPage.as_view(), name="tasks"),
    path('superadmin/tasks/dispatch_cron', core_superadmin.HandleScheduleCronTask.as_view(), name="tasks_dispatch_cron"),
    path('superadmin/tasks/replace_links', core_superadmin.HandleUpdateLinksTask.as_view(), name="tasks_replace_links"),
    path('superadmin/tasks/elasticsearch', core_superadmin.HandleElasticsearchTask.as_view(), name="tasks_elasticsearch"),
    path('superadmin/scanlog', core_superadmin.ScanLog.as_view(), name='scanlog'),
    path('superadmin/auditlog', core_superadmin.AuditLog.as_view()),
    path('superadmin/group_copy', core_superadmin.GroupCopyView.as_view()),
    path('superadmin/optional_features', core_superadmin.OptionalFeatures.as_view(), name="optional_features"),
    path('superadmin/optional_features/profileset/add', core_superadmin.profileset_add, name="optional_features_add_profile_field"),
    path('superadmin/optional_features/profileset/edit/<str:pk>', core_superadmin.profileset_edit, name="optional_features_edit_profile_field"),
    path('superadmin/optional_features/profileset/delete/<str:pk>', core_superadmin.profileset_delete, name="optional_features_delete_profile_field"),
    path('superadmin/support_contract', core_superadmin.SupportContract.as_view()),
    path('superadmin/agreements', core_superadmin.agreements),
    path('superadmin/meetings', core_superadmin.meetings_settings, name='superadmin_meetings_settings'),
    path('graphql', GraphQLView.as_view(schema=schema, extensions=[OpenTracingExtensionSync], introspection=settings.DEBUG), name='graphql'),

    path('file/download/<uuid:file_id>', file_views.download, name='download'),
    path('file/download/<uuid:file_id>/<str:file_name>', file_views.download, name='download'),

    path('file/embed/<uuid:file_id>', file_views.embed, name='embed'),
    path('file/embed/<uuid:file_id>/<str:file_name>', file_views.embed, name='embed'),

    path('file/thumbnail/<uuid:file_id>', file_views.thumbnail, name='thumbnail'),
    path('file/featured/<uuid:entity_guid>', file_views.featured, name='featured'),

    path('attachment/<uuid:attachment_id>', core_views.attachment, name='attachment'),
    # old url for backwards compatability
    path('attachment/<str:attachment_type>/<uuid:attachment_id>', core_views.attachment, name='attachment'),

    path('agreement/<slug:slug>', tenants_views.site_agreement_version_document, name="agreement"),
    path('custom_agreement/<int:custom_agreement_id>', core_views.site_custom_agreement, name="custom_agreement"),

    path('bulk_download', file_views.bulk_download, name='bulk_download'),
    path('download_rich_description_as/<uuid:entity_id>/<str:file_type>', core_views.download_rich_description_as, name='download_rich_description_as'),

    path('events/view/guest-list', event_views.check_in, name='check_in'),

    path('exporting/content/selected', core_views.export_selected_content, name='selected_content_export'),
    path('exporting/content/<str:content_type>', core_views.export_content, name='content_export_type'),
    path('exporting/group/<uuid:group_id>', core_views.export_group_members, name='group_members_export'),
    path('exporting/event/<uuid:event_id>', event_views.export, name='event_export'),
    path('exporting/calendar/', event_views.export_calendar, name='event_calendar_export'),
    path('exporting/users', user_views.export, name='users_export'),
    path('exporting/group-owners', core_views.export_groupowners, name='group_owners_export'),

    path('qr/url/<uuid:entity_id>', core_views.get_url_qr, name='url_qr'),
    path('qr/access/<uuid:entity_id>', event_views.get_access_qr, name='access_qr'),

    path('comment/confirm/<uuid:entity_id>', core_views.comment_confirm, name='comment_confirm'),

    path('onboarding', core_views.onboarding, name='onboarding'),
    path('unsupported_browser', core_views.unsupported_browser, name='unsupported_browser'),

    path('edit_email_settings/<str:token>', core_views.edit_email_settings, name='edit_email_settings'),
    path('custom.css', core_views.custom_css),
    path('favicon.png', core_views.favicon),
    path('robots.txt', core_views.robots_txt),
    path('service-worker.js', core_views.ServiceWorkerView.as_view(), name='service_worker'),
    path('sitemap.xml', cache_page(3600)(sitemap), {'sitemaps': sitemaps}, name='sitemap'),

    path('flow/', include('flow.urls')),
    path('profile_sync_api/', include('profile_sync.urls')),
    path('api/site_info/', concierge_views.get_site_info, name="site_info"),
    path('api/profile/update/', concierge_views.profile_updated, name="profile_updated"),
    path('api/profile/ban/', concierge_views.ban_user, name="profile_banned"),

    # Include elgg url's for redirects
    path('', include('elgg.urls')),

    # Default catch all URL's
    re_path(r'^.*\/view\/(?P<entity_id>[0-9A-Fa-f-]+)\/(?:[^\/.]+)$', core_views.entity_view, name='entity_view'),
    re_path(r'.*', core_views.default, name='default')
]

handler404 = 'core.views.default'


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response

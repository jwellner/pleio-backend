from django.views.generic import RedirectView
from django.urls import re_path
from .views import redirect_view, redirect_download, redirect_friendly_url

urlpatterns = [
    re_path(r'^mod/file/graphics/icons/(?P<path>.*\..*)$',
        RedirectView.as_view(url='/static/file-icons/%(path)s', permanent=False)),

    # Match old ID's and try to redirect
    re_path(r'view\/(?P<entity_id>[0-9]+)\/(?:[^\/.]+)$', redirect_view, name='redirect_view'),
    re_path(r'cms\/view\/([0-9]+)\/[\w-]+\/(?P<entity_id>[0-9]+)$', redirect_view, name='redirect_view'),
    re_path(r'groups\/view\/([0-9]+)\/[\w-]+\/files/(?P<entity_id>[0-9]+)$', redirect_view, name='redirect_view'),
    re_path(r'file\/download\/(?P<file_id>[0-9]+)', redirect_download, name='redirect_download'),
    re_path(r'^(?P<friendly_url>[\w-]+)$', redirect_friendly_url, name='redirect_friendly_url')
]
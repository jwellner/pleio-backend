import json
from core.resolvers.query_site import get_settings
from core import config
from core.models import Entity
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import Truncator

def default(request):

    metadata = {
        "description" : config.DESCRIPTION,
        "og:title" : config.NAME,
        "og:description": config.DESCRIPTION
    }

    context = {
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings()),
        'metadata': metadata,
        'config': config
    }

    return render(request, 'react.html', context)

def entity_view(request, entity_id=None, entity_title=None):
    user = request.user

    entity = None
    metadata = {
        "description" : config.DESCRIPTION,
        "og:title" : config.NAME,
        "og:description": config.DESCRIPTION
    }

    if entity_id:
        try:
            entity = Entity.objects.visible(user).select_subclasses().get(id=entity_id)
        except ObjectDoesNotExist:
            pass

    if entity:
        metadata["description"] = Truncator(entity.description).words(26).replace("\"", "")
        metadata["og:title"] = entity.title
        metadata["og:type"] = 'article'
        if hasattr(entity, 'featured_image') and entity.featured_image:
            metadata["og:image"] = request.build_absolute_uri(entity.featured_image.url)
        if hasattr(entity, 'featured_video') and entity.featured_video:
            metadata["og:video"] = entity.featured_video
        metadata["og:url"] = request.build_absolute_uri(request.path)
        metadata["og:site_name"] = config.NAME
        metadata["article:published_time"] = entity.created_at.strftime("%Y-%m-%d %H:%M")
        metadata["article:modified_time"] = entity.updated_at.strftime("%Y-%m-%d %H:%M")

    context = {
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings()),
        'metadata': metadata,
        'config': config
    }

    return render(request, 'react.html', context)

def logout(request):
    # should find out how we can make this better. OIDC logout only allows POST
    LogoutView.as_view()(request)

    return redirect('/')

def login(request):
    return redirect('oidc_authentication_init')

def oidc_failure(request):
    return redirect(settings.OIDC_OP_LOGOUT_ENDPOINT)

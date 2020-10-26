import json
from core.resolvers.query_site import get_settings
from core import config
from core.models import Entity, UserProfileField, SiteAccessRequest
from core.lib import access_id_to_acl, get_default_email_context, tenant_schema
from core.forms import OnboardingForm, RequestAccessForm
from core.constances import USER_ROLES
from user.models import User
from core.tasks import send_mail_multi
from django.utils.translation import ugettext_lazy
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import Truncator
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

def default(request, exception=None):
    # pylint: disable=unused-argument

    metadata = {
        "description" : config.DESCRIPTION,
        "og:title" : config.NAME,
        "og:description": config.DESCRIPTION
    }

    context = {
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings()),
        'metadata': metadata
    }

    return render(request, 'react.html', context)

def entity_view(request, entity_id=None, entity_title=None):
    # pylint: disable=unused-argument
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
        status_code = 200
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
    else:
        status_code = 404

    context = {
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings()),
        'metadata': metadata
    }

    return render(request, 'react.html', context, status=status_code)

def logout(request):
    # should find out how we can make this better. OIDC logout only allows POST
    LogoutView.as_view()(request)

    return redirect(settings.OIDC_OP_LOGOUT_ENDPOINT)

def login(request):
    if request.GET.get('invitecode', None):
        request.session['invitecode'] = request.GET.get('invitecode')

    return redirect('oidc_authentication_init')

def oidc_failure(request):
    return redirect(settings.OIDC_OP_LOGOUT_ENDPOINT)

def request_access(request):
    # pylint: disable=too-many-nested-blocks
    claims = request.session.get('request_access_claims', None)

    if not claims:
        return redirect('/')

    if request.POST:
        form = RequestAccessForm(request.POST)

        if form.is_valid():
            send_notification = False

            try:
                access_request = SiteAccessRequest.objects.get(email=claims.get('email'))
            except ObjectDoesNotExist:
                access_request = SiteAccessRequest(
                    email=claims.get('email'),
                    name=claims.get('name'),
                    claims=claims
                )
                access_request.save()
                send_notification = True

                # Only send admin mail on first request.
                admins = User.objects.filter(roles__contains=[USER_ROLES.ADMIN])

            if send_notification:
                context = get_default_email_context(request)
                context['request_name'] = claims.get('name')
                context['site_admin_url'] = context['site_url'] + '/admin2'
                subject = ugettext_lazy("New access request for %(site_name)s") % {'site_name': context["site_name"]}

                for admin in admins:
                    context['admin_name'] = admin.name
                    send_mail_multi.delay(tenant_schema(), subject, 'email/site_access_request.html', context, admin.email)

            return redirect('access_requested')
        
    form = RequestAccessForm(initial={'request_access': True})    

    context = {
        'name': claims.get('name'),
        'email': claims.get('email'),
        'form': form
    }

    return render(request, 'registration/request.html', context)

def access_requested(request):
    return render(request, 'registration/requested.html')

@login_required
def onboarding(request):
    user = request.user

    if request.POST:
        form = OnboardingForm(request.POST, user=user)
        if form.is_valid():
            data = form.cleaned_data
            
            for profile_field in form.profile_fields:
                if profile_field.field_type == 'multi_select_field':
                    if data[profile_field.name]:
                        value = ",".join(data[profile_field.name])
                    else:
                        value = ''
                elif profile_field.field_type == 'date_field':
                    if data[profile_field.name]:
                        value = data[profile_field.name].strftime('%Y-%m-%d')
                    else:
                        value = ''
                else:
                    if data[profile_field.name]:
                        value = data[profile_field.name]
                    else:
                        value = ''

                try:
                    user_profile_field = UserProfileField.objects.get(user_profile=user.profile, profile_field=profile_field)
                    user_profile_field.value = value
                    user_profile_field.save()
                except ObjectDoesNotExist:
                    user_profile_field = UserProfileField.objects.create(
                        user_profile=user.profile,
                        profile_field=profile_field,
                        value=value,
                        read_access=access_id_to_acl(user, config.DEFAULT_ACCESS_ID)
                    )

            # Don't show onboarding again for new users:
            if not user.login_count:
                user.login_count = 1
                user.save()

            return HttpResponseRedirect('/')

    else:
        form = OnboardingForm(user=user)

    context = {
        'is_new_user': bool(not user.login_count),
        'is_profile_complete': user.is_profile_complete,
        'form': form,
    }

    return render(request, 'onboarding.html', context)

@require_GET
def robots_txt(request):
    if config.ENABLE_SEARCH_ENGINE_INDEXING:
        lines = [
            "User-Agent: *",
            f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
            "Disallow: /user",
            "Disallow: /search",
            "Disallow: /search/",
            "Disallow: /tags",
            "Disallow: /tags/",
        ]
    else:
        lines = [
            "User-Agent: *",
            "Disallow: /",
        ]

    return HttpResponse("\n".join(lines), content_type="text/plain")

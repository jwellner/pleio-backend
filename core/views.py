import csv
import json
import logging

from core.mail_builders.site_access_request import schedule_site_access_request_mail
from core.models.agreement import CustomAgreement

import qrcode
from core.resolvers.query_site import get_settings
from core import config
from core.models import (
    Entity, Group, UserProfileField, SiteAccessRequest, ProfileField, Attachment,
    CommentRequest, Comment
)
from core.lib import (
    access_id_to_acl, tenant_schema,
    get_exportable_content_types, get_model_by_subtype, datetime_isoformat, get_base_url, is_schema_public
)
from core.forms import EditEmailSettingsForm, OnboardingForm, RequestAccessForm
from core.constances import USER_ROLES, OIDC_PROVIDER_OPTIONS
from core.utils.mail import UnsubscribeTokenizer, EmailSettingsTokenizer
from user.models import User
from event.lib import get_url
from django.utils.translation import gettext as _
from core.auth import oidc_provider_logout_url
from django.core import signing
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.text import Truncator, slugify
from django.utils.http import urlencode
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.http import Http404, HttpResponse, HttpResponseRedirect, StreamingHttpResponse, HttpResponseNotFound
from django.contrib.auth import login as auth_login
from datetime import datetime

logger = logging.getLogger(__name__)


def default(request, exception=None):
    # pylint: disable=unused-argument

    if is_schema_public():
        return render(request, 'domain_placeholder.html', status=404)

    metadata = {
        "description": config.DESCRIPTION,
        "og:title": config.NAME,
        "og:description": config.DESCRIPTION
    }

    context = {
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
        'json_settings': json.dumps(get_settings()),
        'metadata': metadata,
    }

    return render(request, 'react.html', context)


def entity_view(request, entity_id=None, entity_title=None):
    # pylint: disable=unused-argument
    user = request.user

    entity = None

    metadata = {
        "description": config.DESCRIPTION,
        "og:title": config.NAME,
        "og:description": config.DESCRIPTION
    }

    if entity_id:
        try:
            entity = Entity.objects.visible(user).select_subclasses().get(id=entity_id)
        except ObjectDoesNotExist:
            pass

    if not entity:
        try:
            entity = Entity.objects.draft(user).select_subclasses().get(id=entity_id)
        except ObjectDoesNotExist:
            pass

    if entity:
        status_code = 200
        if hasattr(entity, 'description') and entity.description:
            metadata["description"] = Truncator(entity.description).words(26).replace("\"", "")
            metadata["og:description"] = metadata["description"]
        metadata["og:title"] = entity.title
        metadata["og:type"] = 'article'
        if hasattr(entity, 'featured_image_url') and entity.featured_image_url:
            metadata["og:image"] = request.build_absolute_uri(entity.featured_image_url)
        if hasattr(entity, 'featured_video') and entity.featured_video:
            metadata["og:video"] = entity.featured_video
        metadata["og:url"] = request.build_absolute_uri(request.path)
        metadata["og:site_name"] = config.NAME
        metadata["article:published_time"] = entity.created_at.strftime("%Y-%m-%d %H:%M")
        metadata["article:modified_time"] = entity.updated_at.strftime("%Y-%m-%d %H:%M")
    else:
        try:
            entity = Group.objects.visible(user).get(id=entity_id)
            status_code = 200
        except ObjectDoesNotExist:
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

    return redirect(oidc_provider_logout_url(request))


def login(request):
    if request.GET.get('invitecode', None):
        request.session['invitecode'] = request.GET.get('invitecode')

    query_args = {}
    redirect_url = None

    if config.IDP_ID and not request.GET.get('login_credentials'):
        query_args["idp"] = config.IDP_ID

    if request.GET.get('next'):
        query_args["next"] = request.GET.get('next')

    if len(config.OIDC_PROVIDERS) == 1:
        query_args["provider"] = config.OIDC_PROVIDERS[0]
        # only redirect when there is a single provider configured otherwise show login page
        redirect_url = reverse('oidc_authentication_init') + '?' + urlencode(query_args)

    if redirect_url:
        return redirect(redirect_url)

    context = {
        'next': request.GET.get('next', ''),
        'constants': {
            'OIDC_PROVIDER_OPTIONS': OIDC_PROVIDER_OPTIONS,
        },
    }
    return render(request, 'registration/login.html', context)


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
            if not SiteAccessRequest.objects.filter(email=claims.get('email')).exists():
                SiteAccessRequest.objects.create(
                    email=claims.get('email'),
                    name=claims.get('name'),
                    claims=claims
                )
                for admin in User.objects.filter(roles__contains=[USER_ROLES.ADMIN]):
                    schedule_site_access_request_mail(name=claims.get('name'),
                                                      admin=admin)

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


def onboarding(request):
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks

    user = request.user
    claims = request.session.get('onboarding_claims', None)

    if not request.user.is_authenticated and not claims:
        return HttpResponseRedirect('/')

    if not config.ONBOARDING_INTRO and not ProfileField.objects.filter(is_in_onboarding=True).first():
        return HttpResponseRedirect('/')

    if request.POST:
        form = OnboardingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            if not user.is_authenticated and claims:
                user = User.objects.get_or_create_claims(claims)

                logger.info("Onboarding is valid, new user %s created", user.email)

                auth_login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
                del request.session['onboarding_claims']

            for profile_field in form.profile_fields:
                if profile_field.field_type == 'multi_select_field':
                    if data[profile_field.guid]:
                        value = ",".join(data[profile_field.guid])
                    else:
                        value = ''
                elif profile_field.field_type == 'date_field':
                    if data[profile_field.guid]:
                        value = data[profile_field.guid].strftime('%Y-%m-%d')
                    else:
                        value = ''
                else:
                    if data[profile_field.guid]:
                        value = data[profile_field.guid]
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

            return HttpResponseRedirect('/')

    else:
        initial_values = {}

        if user.is_authenticated:
            # get initial values from user
            user_profile_fields = UserProfileField.objects.filter(user_profile=user.profile).all()
            for user_profile_field in user_profile_fields:
                # only set initial value if it is not null
                if user_profile_field.value:
                    if user_profile_field.profile_field.field_type == "multi_select_field":
                        value = user_profile_field.value.split(',')
                    elif user_profile_field.profile_field.field_type == "date_field":
                        # date is stored in format YYYY-mm-dd
                        try:
                            date = datetime.strptime(user_profile_field.value, '%Y-%m-%d')
                            value = date.strftime('%d-%m-%Y')
                        except ValueError as e:
                            logger.error('Unable to parse profile field date: %s', e)
                            value = ""
                    else:
                        value = user_profile_field.value

                    initial_values[user_profile_field.profile_field.guid] = value

        form = OnboardingForm(initial=initial_values)

    context = {
        'form': form,
    }

    return render(request, 'onboarding.html', context)


@cache_control(public=True, max_age=15724800)
def custom_css(request):
    return HttpResponse(config.CUSTOM_CSS, content_type="text/css")


@cache_control(public=True)
def favicon(request):
    if config.FAVICON:
        return redirect(config.FAVICON)
    return redirect("/static/apple-touch-icon.png")


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


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export_group_members(request, group_id=None):
    # pylint: disable=too-many-locals
    # TODO: add tests
    user = request.user

    if not user.is_authenticated:
        raise Http404("User not authenticated")

    if not config.GROUP_MEMBER_EXPORT:
        raise Http404("Export could not be performed")

    try:
        group = Group.objects.get(id=group_id)
    except ObjectDoesNotExist:
        raise Http404("Group not found")

    if not group.can_write(user):
        raise Http404("Group not found")

    headers = ['guid', 'name', 'email', 'member since', 'last login']

    subgroups = group.subgroups.all()
    subgroup_names = subgroups.values_list('name', flat=True)
    headers.extend(subgroup_names)

    rows = [headers]

    for membership in group.members.filter(type__in=['admin', 'owner', 'member']):
        member = membership.user
        if not member.is_active:
            continue

        email = member.email

        member_subgroups = member.subgroups.all()
        subgroup_memberships = []

        for subgroup in subgroups:
            if subgroup in member_subgroups:
                subgroup_memberships.append(True)
            else:
                subgroup_memberships.append(False)
        row = [str(member.id), member.name, email, membership.created_at, member.last_login]
        row.extend(subgroup_memberships)
        rows.append(row)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    writer.writerow(headers)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="' + group.name + '.csv"'

    return response


def export_content(request, content_type=None):
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not logged in")

    if not user.has_role(USER_ROLES.ADMIN):
        raise Http404("Not admin")

    if not content_type:
        raise Http404("Not found")

    exportable_content_types = [d['value'] for d in get_exportable_content_types()]

    if content_type not in exportable_content_types:
        raise Http404("Content type " + content_type + " can not be exported")

    Model = get_model_by_subtype(content_type)
    entities = Model.objects.all()

    def is_included_related_field(field):
        if field.name == 'owner':
            return True
        return False

    def stream(items, pseudo_buffer, Model):
        # pylint: disable=unidiomatic-typecheck
        fields = []
        field_names = []
        for field in Model._meta.get_fields():
            if (
                    type(field) in [models.OneToOneRel, models.ForeignKey, models.ManyToOneRel, GenericRelation, GenericForeignKey]
                    and not is_included_related_field(field)
            ):
                continue
            fields.append(field)
            field_names.append(field.name)

        # if more fields needed, refactor
        field_names.append('url')
        field_names.append('owner_url')

        writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
        yield writer.writerow(field_names)

        def get_data(entity, fields):
            field_values = []
            for field in fields:
                field_value = field.value_from_object(entity)
                if field.get_internal_type() == 'DateTimeField':
                    try:
                        field_value = datetime_isoformat(field_value)
                    except Exception:
                        pass
                field_values.append(field_value)

            # if more fields needed, refactor
            domain = request.tenant.get_primary_domain().domain

            url = entity.url if hasattr(entity, 'url') else ''
            field_values.append(f"https://{domain}{url}")

            owner_url = f"{entity.owner.url}" if hasattr(entity, 'owner') else ''
            field_values.append(f"https://{domain}{owner_url}")

            return field_values

        for item in items:
            yield writer.writerow(get_data(item, fields))

    response = StreamingHttpResponse(
        streaming_content=(stream(entities, Echo(), Model)),
        content_type='text/csv',
    )

    filename = content_type + '-export.csv'
    response['Content-Disposition'] = 'attachment;filename=' + filename

    return response


def export_groupowners(request):
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not logged in")

    if not user.has_role(USER_ROLES.ADMIN):
        raise Http404("Not admin")

    def stream(groups, pseudo_buffer):
        writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
        yield writer.writerow([_("Name"),
                               _("E-mail"),
                               _("Group")])

        for g in groups:
            yield writer.writerow([
                g.owner.name,
                g.owner.email,
                g.name,
            ])

    response = StreamingHttpResponse(
        streaming_content=(stream(Group.objects.all(), Echo())),
        content_type='text/csv',
    )

    filename = 'group-owners.csv'
    response['Content-Disposition'] = 'attachment;filename=' + filename

    return response


def attachment(request, attachment_id, attachment_type=None):
    # pylint: disable=unused-argument
    user = request.user

    size = request.GET.get('size', None)

    try:
        attachment = Attachment.objects.get(id=attachment_id)

        if not attachment.can_read(user):
            raise Http404("File not found")

        return_file = attachment

        if size:
            resized_image = attachment.get_resized_image(size)

            if resized_image:
                return_file = resized_image
            else:
                return redirect(attachment.url)

        attachment_or_inline = "attachment" if not return_file.mime_type else "inline"

        response = StreamingHttpResponse(streaming_content=return_file.upload.open(), content_type=return_file.mime_type)
        response['Content-Length'] = return_file.upload.size
        response['Content-Disposition'] = f"{attachment_or_inline}; filename=%s" % return_file.name
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")


def comment_confirm(request, entity_id):
    try:
        entity = Entity.objects.select_subclasses().get(id=entity_id)
    except ObjectDoesNotExist:
        raise Http404("Entity not found")

    comment_request = CommentRequest.objects.filter(
        object_id=entity.id,
        code=request.GET.get('code', None),
        email=request.GET.get('email', None)
    ).first()

    if comment_request:
        Comment.objects.create(
            container=entity,
            rich_description=comment_request.rich_description,
            email=comment_request.email,
            name=comment_request.name
        )

        comment_request.delete()

    return redirect(entity.url)


def edit_email_settings(request, token):
    user = None

    try:
        tokenizer = EmailSettingsTokenizer()
        user = tokenizer.unpack(token)
    except (signing.BadSignature, ObjectDoesNotExist):
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        form = EditEmailSettingsForm(request.POST)

        if form.is_valid():
            user.profile.receive_notification_email = form.cleaned_data['notifications_email_enabled']
            user.profile.overview_email_interval = form.cleaned_data['overview_email_enabled']
            user.profile.save()
            messages.success(request, _('Your changes are saved'))
            return HttpResponseRedirect(request.path)

    initial_dict = {
        'notifications_email_enabled': user.profile.receive_notification_email,
        'overview_email_enabled': user.profile.overview_email_interval,
    }

    form = EditEmailSettingsForm(initial=initial_dict)

    context = {
        'user_name': user.name,
        'site_url': get_base_url(),
        'site_name': config.NAME,
        'form': form
    }

    return render(request, 'edit_email_settings.html', context)


def unsupported_browser(request):
    return render(request, 'unsupported_browser.html')


def get_url_qr(request, entity_id=None):
    # Only implemented for Events. Can be adjusted to be used for other entities
    user = request.user

    if not user.is_authenticated:
        raise Http404("Event not found")

    try:
        entity = Entity.objects.visible(user).get_subclass(id=entity_id)
    except ObjectDoesNotExist:
        raise Http404("Event not found")

    url = get_url(entity)
    if hasattr(entity, 'title') and entity.title:
        filename = slugify(entity.title)[:248].removesuffix("-")
    else:
        filename = entity.id

    code = qrcode.make(url)

    response = HttpResponse(content_type='image/png')
    code.save(response, "PNG")
    response['Content-Disposition'] = f'attachment; filename="qr_{filename}.png"'

    return response


def unsubscribe(request, token):
    try:
        user, mail_id, is_expired = UnsubscribeTokenizer().unpack(token)
        list_name = None
        if mail_id == UnsubscribeTokenizer.TYPE_OVERVIEW:
            user.profile.overview_email_interval = 'never'
            list_name = _("Periodic overview")
        elif mail_id == UnsubscribeTokenizer.TYPE_NOTIFICATIONS:
            user.profile.receive_notification_email = False
            list_name = _("Notification overview")
        user.profile.save()

        msg = _("Successfully unsubscribed %(email)s from %(list_name)s") % {
            'email': user.email,
            'list_name': list_name
        }

        if not is_expired:
            messages.success(request, msg)
            return HttpResponseRedirect(EmailSettingsTokenizer().create_url(user))

        return render(request, "unsubscribe.html", {
            "msg": msg
        })
    except Exception as e:
        logger.error("unsubscribe_error: schema=%s, error=%s, type=%s, token=%s", tenant_schema(), str(e), e.__class__, token)
        return HttpResponseNotFound()


def site_custom_agreement(request, custom_agreement_id):
    # pylint: disable=unused-argument
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not logged in")

    if not user.has_role(USER_ROLES.ADMIN):
        raise Http404("Not admin")

    try:
        custom_agreement = CustomAgreement.objects.get(id=custom_agreement_id)

        return_file = custom_agreement

        response = StreamingHttpResponse(streaming_content=return_file.document.open(), content_type='application/pdf')
        response['Content-Length'] = return_file.document.size
        response['Content-Disposition'] = "filename=%s" % return_file.name
        return response

    except ObjectDoesNotExist:
        raise Http404("File not found")

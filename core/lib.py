import ipaddress
import json
import os
import re
import secrets
import tempfile
import mimetypes
import uuid
import html2text
from pytz import timezone
from colour import Color
from core.constances import ACCESS_TYPE
from core import config
from django.apps import apps
from django.conf import settings
from django.core import signing
from django.core.validators import URLValidator
from django.db import connection
from django.utils.text import slugify
from django.utils.translation import ugettext, ugettext_lazy
from enum import Enum

from core.utils.tiptap_parser import Tiptap


class TypeModels(Enum):
    """Can be used to convert GraphQL types to Django models"""

    news = "news.News"
    poll = "poll.Poll"
    discussion = "discussion.Discussion"
    event = "event.Event"
    wiki = "wiki.Wiki"
    question = "question.Question"
    page = "cms.Page"
    blog = "blog.Blog"
    group = "core.Group"
    user = "user.User"
    statusupdate = "activity.StatusUpdate"
    thewire = "activity.StatusUpdate"
    task = "task.Task"
    comment = "core.Comment"
    file = "file.FileFolder"
    folder = "file.FileFolder"


def get_model_by_subtype(subtype):
    """Get Django model by subtype name"""

    try:
        model_name = TypeModels[subtype].value
        return apps.get_model(model_name)
    except AttributeError:
        return None

    return None

def access_id_to_acl(obj, access_id):
    if "type_to_string" in dir(obj) and obj.type_to_string and obj.type_to_string == 'user':
        acl = [ACCESS_TYPE.user.format(obj.id)]
    else:
        acl = [ACCESS_TYPE.user.format(obj.owner.id)]

    if isinstance(access_id, str):
        access_id = int(access_id)

    in_closed_group = False
    if hasattr(obj, 'group') and obj.group:
        in_closed_group = obj.group.is_closed

    # object is in close group, convert public to group access
    if in_closed_group and access_id in (1, 2):
        access_id = 4

    if access_id == 1 and not in_closed_group:
        acl.append(ACCESS_TYPE.logged_in)
    elif access_id == 2 and not in_closed_group:
        acl.append(ACCESS_TYPE.public)
    elif access_id == 4 and obj.group:
        acl.append(ACCESS_TYPE.group.format(obj.group.id))
    elif access_id and access_id >= 10000 and obj.group:
        acl.append(ACCESS_TYPE.subgroup.format(access_id))
    return acl


def get_acl(user):
    """Get user Access List"""

    acl = set([ACCESS_TYPE.public])

    if user.is_authenticated:
        acl.add(ACCESS_TYPE.logged_in)
        acl.add(ACCESS_TYPE.user.format(user.id))

        if user.memberships:
            groups = set(
                ACCESS_TYPE.group.format(membership.group.id) for membership in user.memberships.filter(type__in=['admin', 'owner', 'member'])
                )
            acl = acl.union(groups)
        if user.subgroups:
            subgroups = set(
                ACCESS_TYPE.subgroup.format(subgroup.access_id) for subgroup in user.subgroups.all()
            )
            acl = acl.union(subgroups)

    return acl


def clean_graphql_input(values, always_include=None):
    """ Cleanup resolver input """
    # TODO: what are we going to do with values which kan be omitted or can be NULL

    # Prevent external attachment URLs
    rich_description = values.get("richDescription")
    if rich_description:
        tiptap = Tiptap(rich_description)
        tiptap.check_for_external_urls()

    # Remove items with None values from dict except for timePublished data
    return {k: v for k, v in values.items() if (v is not None) or (k == 'timePublished') or (always_include and (k in always_include))}


def webpack_dev_server_is_available():
    """Return true when webpack developer server is available"""
    # pylint: disable=import-outside-toplevel

    if settings.ENV == 'prod':
        return False

    docker_host = os.environ.get('DOCKER_LOCAL_MACHINE', None)

    if docker_host:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1.0)
                return s.connect_ex((docker_host, 9001)) == 0
            except Exception:
                return False
    return False

def get_access_id(acl):
    for x in acl:
        if x.startswith("group:"):
            return 4
    if ACCESS_TYPE.public in acl:
        return 2
    if ACCESS_TYPE.logged_in in acl:
        return 1
    return 0


def get_access_ids(obj=None):
    """Return the available accessId's"""
    accessIds = []
    accessIds.append({ 'id': 0, 'description': ugettext("Just me") })

    if isinstance(obj, apps.get_model('core.Group')):
        accessIds.append({ 'id': 4, 'description': ugettext("Group: %(group_name)s") % {'group_name': obj.name} })
        if obj.subgroups:
            for subgroup in obj.subgroups.all():
                accessIds.append({ 'id': subgroup.access_id, 'description': ugettext("Subgroup: %(subgroup_name)s") % {'subgroup_name': subgroup.name} })

    if isinstance(obj, apps.get_model('core.Group')) and obj.is_closed:
        pass
    else:
        accessIds.append({ 'id': 1, 'description': ugettext("Logged in users")})
        if not config.IS_CLOSED:
            accessIds.append({ 'id': 2, 'description': ugettext("Public")})

    return accessIds

def get_activity_filters():
    """TODO: should only return active content"""
    return {
        'contentTypes': [
            {
                'key': 'event',
                'value': ugettext_lazy("Event")
            },
            {
                'key': 'blog',
                'value': ugettext_lazy("Blog")
            },
            {
                'key': 'discussion',
                'value': ugettext_lazy("Discussion")
            },
            {
                'key': 'news',
                'value': ugettext_lazy("News")
            },
            {
                'key': 'statusupdate',
                'value': ugettext_lazy("Update")
            },
            {
                'key': 'question',
                'value': ugettext_lazy("Question")
            },
            {
                'key': 'wiki',
                'value': ugettext_lazy("Wiki pages")
            }
        ]
    }

def generate_object_filename(obj, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join(str(obj.id), filename)

def delete_attached_file(filefield):
    if not filefield:
        return

    file_path = filefield.path
    if os.path.isfile(file_path):
        os.remove(file_path)

def get_field_type(field_type):
    if field_type == 'select_field':
        return 'selectField'
    if field_type == 'date_field':
        return 'dateField'
    if field_type == 'html_field':
        return 'htmlField'
    if field_type == 'multi_select_field':
        return 'multiSelectField'
    return 'textField'


def is_valid_json(string):
    try:
        string = json.loads(string)
    except Exception:
        return False
    return True


def get_base_url():
    try:
        tenant = apps.get_model('tenants.Client').objects.get(schema_name=connection.schema_name)
        return 'https://' + tenant.get_primary_domain().domain
    except Exception:
        return ''


def get_default_email_context(user=None):
    site_url = get_base_url()
    user_url = site_url + user.url if user else ''
    user_name = user.name if user else ''
    site_name = config.NAME
    primary_color = config.COLOR_PRIMARY
    header_color = config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY
    if user:
        signer = signing.TimestampSigner()
        token = signer.sign_object({
            "id": str(user.id),
            "email": user.email
        })
        unsubscribe_url = site_url + '/edit_email_settings/' + token
    else:
        unsubscribe_url = ''

    return {
        'user_name': user_name,
        'user_url': user_url,
        'site_url': site_url,
        'site_name': site_name,
        'primary_color': primary_color,
        'header_color': header_color,
        'unsubscribe_url': unsubscribe_url
    }

def obfuscate_email(email):
    # alter email: example@domain.com -> e******@domain.com
    try:
        email_splitted = email.split("@")
        nr_char = len(email_splitted[0])
        return email_splitted[0][0] + '*'*nr_char + '@' + email_splitted[1]
    except Exception:
        pass
    return ""


def generate_code():
    return secrets.token_hex(10)


def get_exportable_user_fields():
    return [
        {'field_type': 'userField', 'field': 'guid', 'label': 'guid'},
        {'field_type': 'userField', 'field': 'name', 'label': 'name'},
        {'field_type': 'userField', 'field': 'email', 'label': 'email'},
        {'field_type': 'userField', 'field': 'created_at', 'label': 'created_at'},
        {'field_type': 'userField', 'field': 'updated_at', 'label': 'updated_at'},
        {'field_type': 'userField', 'field': 'last_online', 'label': 'last_online'},
        {'field_type': 'userField', 'field': 'banned', 'label': 'banned'},
        {'field_type': 'userField', 'field': 'ban_reason', 'label': 'ban_reason'},
        {'field_type': 'userField', 'field': 'group_memberships', 'label': 'group_memberships'},
        {'field_type': 'userField', 'field': 'receive_newsletter', 'label': 'receive_newsletter'},
        {'field_type': 'userField', 'field': 'created_at_unix', 'label': 'created_at (U)'},
        {'field_type': 'userField', 'field': 'updated_at_unix', 'label': 'updated_at (U)'},
        {'field_type': 'userField', 'field': 'last_online_unix', 'label': 'last_online (U)'},
    ]

def get_exportable_content_types():
    return [
        {"value": "statusupdate", "label": ugettext_lazy("Updates")},
        {"value": "blog", "label": ugettext_lazy("Blogs")},
        {"value": "page", "label": ugettext_lazy("CMS pages")},
        {"value": "discussion", "label": ugettext_lazy("Discussions")},
        {"value": "event", "label": ugettext_lazy("Events")},
        {"value": "file", "label": ugettext_lazy("Files")},
        {"value": "news", "label": ugettext_lazy("News")},
        {"value": "poll", "label": ugettext_lazy("Polls")},
        {"value": "question", "label": ugettext_lazy("Questions")},
        {"value": "task", "label": ugettext_lazy("Tasks")},
        {"value": "wiki", "label": ugettext_lazy("Wiki pages")},
        {"value": "comment", "label": ugettext_lazy("Comments")},
        {"value": "group", "label": ugettext_lazy("Groups")}
    ]

def get_language_options():
    return [{'value': item[0], 'label': item[1]} for item in settings.LANGUAGES]

def tenant_schema():
    return connection.schema_name

def html_to_text(html):
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_tables = True
    h.ignore_images = True
    return h.handle(html)

def get_tmp_file_path(user, suffix= ""):
    folder = os.path.join(tempfile.gettempdir(), tenant_schema(), str(user.id))
    try:
        os.makedirs(folder)
    except FileExistsError:
        pass
    _, temp_file_path = tempfile.mkstemp(dir=folder, suffix=suffix)

    return temp_file_path

def is_valid_domain(domain):
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9]'  # First character of the domain
        r'(?:[a-zA-Z0-9-_]{0,61}[A-Za-z0-9])?\.)'  # Sub domain + hostname
        r'+[A-Za-z0-9][A-Za-z0-9-_]{0,61}'  # First 61 characters of the gTLD
        r'[A-Za-z]$'  # Last character of the gTLD
    )
    try:
        return pattern.match(domain)
    except (UnicodeError, AttributeError):
        return None

def hex_color_tint(hex_color, weight = 0.5):
    try:
        color = Color(hex_color)
    except AttributeError:
        # Add some logging?
        return hex_color

    newR = color.rgb[0] + (1 - color.rgb[0]) * weight
    newG = color.rgb[1] + (1 - color.rgb[1]) * weight
    newB = color.rgb[2] + (1 - color.rgb[2]) * weight
    new = Color(rgb=(newR, newG, newB))
    return new.hex

def datetime_isoformat(obj):
    if obj:
        return obj.astimezone(timezone(settings.TIME_ZONE)).isoformat(timespec="seconds")
    return None

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    try:
        ipv4_version = ipaddress.IPv6Address(x_forwarded_for).ipv4_mapped
        if ipv4_version:
            x_forwarded_for = str(ipv4_version)
    except Exception:
        pass

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_valid_url_or_path(url):
    validate = URLValidator()
    if not url.startswith('http'):
        url = 'https://test.nl' + url
    try:
        validate(url)
        return True
    except Exception:
        return False

def get_mimetype(filepath):
    mimetypes.init()
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        return None
    return mime_type

def map_notification(notification):
    """ get a mapped notification """
    entity = notification.action_object
    performer = apps.get_model('user.User').objects.get(id=notification.actor_object_id)
    entity_group = False
    entity_group_name = ""
    entity_group_url = ""
    if hasattr(entity, 'group') and entity.group:
        entity_group = True
        entity_group_name = entity.group.name
        entity_group_url = entity.group.url

    return {
        'id': notification.id,
        'action': notification.verb,
        'performer_name': performer.name,
        'entity_title': entity.title if hasattr(entity, 'title') else "",
        'entity_description': entity.description if hasattr(entity, 'description') else "",
        'entity_type': entity._meta.verbose_name,
        'entity_group': entity_group,
        'entity_group_name': entity_group_name,
        'entity_group_url': entity_group_url,
        'entity_url': entity.url,
        'type_to_string': entity.type_to_string,
        'timeCreated': notification.timestamp,
        'isUnread': notification.unread
    }

def get_model_name(instance):
    return instance._meta.app_label + '.' + instance._meta.model_name

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

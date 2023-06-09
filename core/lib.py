import base64

import html2text
import ipaddress
import json
import logging
import mimetypes
import os
import re
import secrets
import tempfile
import uuid

from bs4 import BeautifulSoup
from colour import Color
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.validators import URLValidator
from django.db import connection
from django.urls import reverse
from django.utils import timezone as django_timezone
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import ugettext, ugettext_lazy
from enum import Enum
from PIL import Image, UnidentifiedImageError
from pytz import timezone
from urllib.parse import urljoin

from core import config
from core.constances import ACCESS_TYPE
from core.exceptions import IgnoreIndexError, UnableToTestIndex

logger = logging.getLogger(__name__)


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
    task = "task.Task"
    comment = "core.Comment"
    file = "file.FileFolder"
    folder = "file.FileFolder"
    pad = "file.FileFolder"
    externalcontent = 'external_content.ExternalContent'
    externalcontentsource = 'external_content.ExternalContentSource'


def get_model_by_subtype(subtype):
    """Get Django model by subtype name"""

    try:
        model_name = TypeModels[subtype].value
        return apps.get_model(model_name)
    except AttributeError:  # pragma: no cover
        return None


def access_id_to_acl(obj, access_id):
    """
    @tag: acl_methods

    @see also
      * access_id_to_acl(obj: *, access_id: int)
      - get_acl(user: User)
      - get_access_id(acl: [str])
      - get_access_ids(obj: *)

    What are the access id's?
    0: private
    1: logged in
    2: public
    4: Group
    10000+: Subgroup
    """
    from core.models import Group
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
    elif access_id == 4 and getattr(obj, 'group', None):
        acl.append(ACCESS_TYPE.group.format(obj.group.id))
    elif access_id == 4 and isinstance(obj, (Group,)):
        acl.append(ACCESS_TYPE.group.format(obj.id))
    elif access_id and access_id >= 10000 and getattr(obj, 'group', None):
        acl.append(ACCESS_TYPE.subgroup.format(access_id))
    return acl


def get_acl(user):
    """
    @tag: acl_methods

    @see also
      - access_id_to_acl(obj: *, access_id: int)
      * get_acl(user: User)
      - get_access_id(acl: [str])
      - get_access_ids(obj: *)
    """

    acl = set([ACCESS_TYPE.public])

    if user.is_authenticated:
        acl.add(ACCESS_TYPE.logged_in)
        acl.add(ACCESS_TYPE.user.format(user.id))

        if user.memberships:
            groups = set(
                ACCESS_TYPE.group.format(membership.group.id) for membership in
                user.memberships.filter(type__in=['admin', 'owner', 'member'])
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
    allow_none = ['timePublished',
                  'scheduleArchiveEntity',
                  'scheduleDeleteEntity',
                  'groupGuid'] + (always_include or [])
    # TODO: what are we going to do with values which kan be omitted or can be NULL

    # Remove items with None values from dict except for timePublished data
    return {k: v for k, v in values.items() if
            (v is not None) or (k in allow_none)}


def webpack_dev_server_is_available():  # pragma: no cover
    """Return true when webpack developer server is available"""
    # pylint: disable=import-outside-toplevel

    if settings.ENV != 'local':
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
    """
    @tag: acl_methods

    @see also
      - access_id_to_acl(obj: *, access_id: int)
      - get_acl(user: User)
      * get_access_id(acl: [str])
      - get_access_ids(obj: *)
    """
    for x in acl:
        if x.startswith("subgroup:"):
            return int(x.replace("subgroup:", ""))
        if x.startswith("group:"):
            return 4
    if ACCESS_TYPE.public in acl:
        return 2
    if ACCESS_TYPE.logged_in in acl:
        return 1
    return 0


def get_access_ids(obj=None):
    """
    @tag: acl_methods

    @see also
      - access_id_to_acl(obj: *, access_id: int)
      - get_acl(user: User)
      - get_access_id(acl: [str])
      * get_access_ids(obj: *)
    """
    accessIds = []
    accessIds.append({'id': 0, 'description': ugettext("Just me")})

    if isinstance(obj, apps.get_model('core.Group')):
        accessIds.append({'id': 4, 'description': ugettext("Group: %(group_name)s") % {'group_name': obj.name}})
        if obj.subgroups:
            for subgroup in obj.subgroups.all():
                accessIds.append({'id': subgroup.access_id, 'description': ugettext("Subgroup: %(subgroup_name)s") % {
                    'subgroup_name': subgroup.name}})

    if isinstance(obj, apps.get_model('core.Group')) and obj.is_closed:
        pass
    else:
        accessIds.append({'id': 1, 'description': ugettext("Logged in users")})
        if not config.IS_CLOSED:
            accessIds.append({'id': 2, 'description': ugettext("Public")})

    return accessIds


def get_core_hook(hook_name):
    key = "CORE_HOOK_REPOSITORY:%s" % hook_name
    result = cache.get(key)
    if not result:
        result = []
        for app_config in apps.get_app_configs():
            try:
                hook_path = "{}.core_hooks.{}".format(app_config.name, hook_name)
                assert callable(import_string(hook_path))
                result.append(hook_path)
            except ImportError:
                pass
        cache.set(key, result)
    return result


def test_elasticsearch_index(index_name):
    for path in get_core_hook('test_elasticsearch_index'):
        try:
            test_function = import_string(path)
            test_function(index_name)
            return
        except IgnoreIndexError:
            pass

    raise UnableToTestIndex()


def get_hourly_cron_jobs():  # pragma: no cover
    for task_name in get_core_hook("get_hourly_cron_jobs"):
        yield from import_string(task_name)()


def get_activity_filters():
    for hook in get_core_hook('get_activity_filters'):
        hook_function = import_string(hook)
        yield from hook_function()


def get_entity_filters():
    for hook in get_core_hook('get_entity_filters'):
        hook_function = import_string(hook)
        yield from hook_function()


def get_search_filters():
    for hook in get_core_hook('get_search_filters'):
        hook_function = import_string(hook)
        yield from hook_function()


def generate_object_filename(obj, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join(str(obj.id), filename)


def delete_attached_file(filefield):
    if not filefield:
        return

    try:
        file_path = filefield.path
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
    except FileNotFoundError:
        pass


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
        url_schema = "http" if settings.ENV == 'local' else "https"
        url_port = ":8000" if settings.ENV == 'local' else ""
        tenant = apps.get_model('tenants.Client').objects.get(schema_name=connection.schema_name)
        return f'{url_schema}://{tenant.get_primary_domain().domain}{url_port}'
    except Exception:
        return ''


def get_full_url(relative_path):
    if not re.match(r"^https?:\/\/", relative_path):
        return f"{get_base_url()}{relative_path}"
    return relative_path


def get_account_url(relative_path):
    prefix = str(settings.ACCOUNT_API_URL).rstrip('/')
    return urljoin(prefix, relative_path)


def tenant_api_token():
    if not config.TENANT_API_TOKEN:
        config.TENANT_API_TOKEN = str(uuid.uuid4())
    return config.TENANT_API_TOKEN


def tenant_summary(with_favicon=False):
    summary = {
        'url': get_base_url(),
        'name': config.NAME,
        'description': config.DESCRIPTION,
        'api_token': tenant_api_token(),
    }

    if with_favicon and config.FAVICON:
        try:
            from file.models import FileFolder
            file = FileFolder.objects.file_by_path(config.FAVICON)
            summary['favicon'] = os.path.basename(file.upload.path)
            summary['favicon_data'] = file.get_content(wrap=lambda content: base64.encodebytes(content).decode())
        except AttributeError:
            pass

    return summary


def obfuscate_email(email):
    # alter email: example@domain.com -> e******@domain.com
    try:
        email_splitted = email.split("@")
        nr_char = len(email_splitted[0]) - 1
        return email_splitted[0][0] + '*' * nr_char + '@' + email_splitted[1]
    except Exception:
        return ""


def generate_code():
    return secrets.token_hex(10)


def get_exportable_user_fields():
    from user.exporting import ExportUsers
    return [{'field_type': 'userField',
             'field': r.field,
             'label': r.label,
             } for r in ExportUsers.AVAILABLE_SERIALIZERS]


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


def is_schema_public():
    return connection.schema_name == 'public'


def tenant_schema():
    return connection.schema_name


def html_to_text(html):
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_tables = True
    h.ignore_images = True
    return h.handle(html)


def replace_html_img_src(html, user, file_type):
    from file.models import FileFolder

    def get_img_src(path, user):
        if file_type in ['odt']:
            try:
                attachment_id = path.split('/')[2]
                attachment = FileFolder.objects.get(id=attachment_id)
                if attachment.can_read(user):
                    path = attachment.upload.path
            except Exception:
                pass
        elif file_type == 'html':
            path = get_base_url() + path
        return path

    soup = BeautifulSoup(html, "html.parser")
    for img in soup.findAll('img'):
        img['src'] = get_img_src(img['src'], user)
    return str(soup)


def get_tmp_file_path(user, suffix=""):
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


def hex_color_tint(hex_color, weight=0.5):
    try:
        color = Color(hex_color)
    except AttributeError:
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


def datetime_format(obj, seconds=False):
    if isinstance(obj, django_timezone.datetime):
        obj = obj.astimezone(django_timezone.get_current_timezone())
        if seconds:
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return obj.strftime("%Y-%m-%d %H:%M")
    return ""


def datetime_utciso(value):
    if isinstance(value, (django_timezone.datetime,)):
        return value.astimezone(django_timezone.utc).isoformat()
    return ""


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    try:
        ipv4_version = ipaddress.IPv6Address(x_forwarded_for).ipv4_mapped

        if ipv4_version:  # pragma: no cover
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


def get_basename(filepath):
    return os.path.basename(filepath)


def get_filesize(filepath):
    return os.path.getsize(filepath)


def get_model_name(instance):
    return instance._meta.app_label + '.' + instance._meta.model_name


def get_file_checksum(fh):
    try:
        from hashlib import md5
        return md5(fh.read()).hexdigest()
    except Exception:
        pass


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


class NumberIncrement:
    def __init__(self, n=0):
        self.n = n

    def next(self):
        try:
            return self.n
        finally:
            self.n = self.n + 1


def early_this_morning(reference=None):
    reference = reference or django_timezone.localtime()
    return reference - django_timezone.timedelta(hours=reference.hour,
                                                 minutes=reference.minute,
                                                 seconds=reference.second,
                                                 microseconds=reference.microsecond)


def str_to_datetime(datetime_str):
    if not datetime_str:
        return None
    result = django_timezone.datetime.fromisoformat(datetime_str)
    if django_timezone.is_aware(result):
        return result.astimezone(django_timezone.get_current_timezone())

    return django_timezone.make_aware(result).astimezone(django_timezone.get_current_timezone())


def strip_exif(upload_field):
    try:
        filepath = upload_field.path
        image = Image.open(filepath)
        if image.getexif():
            # Not all plugins support animated images (https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.is_animated)
            is_animated = getattr(image, "is_animated", False)
            image.save(filepath, save_all=is_animated)
    except (FileNotFoundError, ValueError,
            UnidentifiedImageError):
        pass


def validate_token(request, token):
    if not token:
        return False

    try:
        if str(request.META['HTTP_AUTHORIZATION']) == str('Bearer ' + token):
            return True
    except Exception:
        pass

    try:
        if str(request.META['headers']['Authorization']) == str('Bearer ' + token):
            return True
    except Exception:
        pass
    return False


def get_page_tag_filters():
    defaults = [{"contentType": ct,
                 "showTagFilter": tf,
                 "showTagCategories": []
                 } for ct, tf in [('news', True),
                                  ('blog', True),
                                  ('question', True),
                                  ('discussion', True),
                                  ('event', False)]]
    stored_settings = {f['contentType']: f for f in config.PAGE_TAG_FILTERS if 'contentType' in f}

    # Ensure consistent number of settings for the applicable content types.
    for setting in defaults:
        if setting['contentType'] in stored_settings:
            yield stored_settings[setting['contentType']]
        else:
            yield setting


def task_status(task_id):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    print(result.status)


def registration_url():
    return reverse('oidc_authentication_init') + '?provider=pleio&method=register'

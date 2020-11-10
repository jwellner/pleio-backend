import json
import os
import secrets
import tempfile
from core.constances import ACCESS_TYPE, COULD_NOT_SAVE
from core import config
from django.apps import apps
from django.conf import settings
from django.db import connection
from django.utils.text import slugify
from graphql import GraphQLError
from enum import Enum
import html2text
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.constants import ENTITY_TYPES, BLOCK_TYPES


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

    if in_closed_group and access_id in (1, 2):
        raise GraphQLError(COULD_NOT_SAVE)

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

def remove_none_from_dict(values):
    """Cleanup resolver input: remove keys with None values"""

    return {k:v for k,v in values.items() if v is not None}

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

def get_access_id(obj):
    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0


def get_access_ids(obj=None):
    """Return the available accessId's"""
    accessIds = []
    accessIds.append({ 'id': 0, 'description': 'Alleen eigenaar'})

    if isinstance(obj, apps.get_model('core.Group')):
        accessIds.append({ 'id': 4, 'description': "Group: {}".format(obj.name)})
        if obj.subgroups:
            for subgroup in obj.subgroups.all():
                accessIds.append({ 'id': subgroup.access_id, 'description': "Subgroup: {}".format(subgroup.name)})

    if isinstance(obj, apps.get_model('core.Group')) and obj.is_closed:
        pass
    else:
        accessIds.append({ 'id': 1, 'description': 'Gebruikers van deze site'})
        accessIds.append({ 'id': 2, 'description': 'Iedereen (publiek zichtbaar)'})

    return accessIds

def get_activity_filters():
    """TODO: should only return active content"""
    return {
        'contentTypes': [
            {
                'key': 'event',
                'value': 'Agenda-Item'
            },
            {
                'key': 'blog',
                'value': 'Blog'
            },
            {
                'key': 'discussion',
                'value': 'Discussie'
            },
            {
                'key': 'news',
                'value': 'Nieuws'
            },
            {
                'key': 'statusupdate',
                'value': 'Update'
            },
            {
                'key': 'question',
                'value': 'Vraag'
            },
        ]
    }

def generate_object_filename(obj, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join(str(obj.id), filename)


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
    except ValueError:
        return False
    return True


def get_base_url(request):
    return 'https://' + request.get_host()


def get_default_email_context(request):
    user_name = ""
    site_url = get_base_url(request)
    user_url = site_url
    if hasattr(request.user, 'url'):
        user_url = site_url + request.user.url
    if hasattr(request.user, 'name'):
        user_name = request.user.name
    site_name = config.NAME
    primary_color = config.COLOR_PRIMARY
    return {'user_name': user_name, 'user_url': user_url, 'site_url': site_url, 'site_name': site_name, 'primary_color': primary_color}


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
        {'field_type': 'userField', 'field': 'receive_newsletter', 'label': 'receive_newsletter'}
    ]

def tenant_schema():
    return connection.get_schema()

def html_to_text(html):
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_tables = True
    h.ignore_images = True
    return h.handle(html)

def draft_to_html(draft_string):
    if not is_valid_json(draft_string):
        return draft_string

    def image(props):
        return DOM.create_element('img', {
            'src': props.get('src'),
            'alt': props.get('alt'),
        })

    def link(props):
        return DOM.create_element("a", {
            "href": props["url"]
        }, props["children"])

    def block_fallback(props):
        # pylint: disable=unused-argument
        return None

    def entity_fallback(props):
        # pylint: disable=unused-argument
        return None

    config = {
        'block_map': dict(BLOCK_MAP, **{
            BLOCK_TYPES.FALLBACK: block_fallback
        }),
        'style_map': dict(STYLE_MAP, **{
        }),
        'entity_decorators': {
            # Map entities to components so they can be rendered with their data.
            ENTITY_TYPES.IMAGE: image,
            ENTITY_TYPES.LINK: link,
            # Lambdas work too.
            ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element('hr'),
            # Discard those entities.
            ENTITY_TYPES.EMBED: None,
            # Provide a fallback component (advanced).
            ENTITY_TYPES.FALLBACK: entity_fallback,
        }
    }

    exporter = HTML(config)

    html = exporter.render(json.loads(draft_string))

    return html

def get_tmp_file_path(user, suffix= ""):
    folder = os.path.join(tempfile.gettempdir(), tenant_schema(), str(user.id))
    try:
        os.makedirs(folder)
    except FileExistsError:
        pass
    _, temp_file_path = tempfile.mkstemp(dir=folder, suffix=suffix)

    return temp_file_path

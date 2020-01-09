import json
import os
import secrets
from core.constances import ACCESS_TYPE
from core import config
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.apps import apps
from django.template.loader import get_template
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.text import slugify
from enum import Enum


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
    user = "core.User"
    status_update = "activity.StatusUpdate"
    thewire = "activity.StatusUpdate"
    task = "task.Task"


def get_model_by_subtype(subtype):
    """Get Django model by subtype name"""

    try:
        model_name = TypeModels[subtype].value
        return apps.get_model(model_name)
    except AttributeError:
        return None

    return None

def access_id_to_acl(obj, access_id):
    if "type_to_string" in dir(obj) and obj.type_to_string() and obj.type_to_string() == 'user':
        acl = [ACCESS_TYPE.user.format(obj.id)]
    else:
        acl = [ACCESS_TYPE.user.format(obj.owner.id)]

    in_closed_group = False
    if hasattr(obj, 'group') and obj.group:
        in_closed_group = obj.group.is_closed

    if access_id == 1 and not in_closed_group:
        acl.append(ACCESS_TYPE.logged_in)
    elif access_id == 2 and not in_closed_group:
        acl.append(ACCESS_TYPE.public)
    elif access_id == 4 and obj.group:
        acl.append(ACCESS_TYPE.group.format(obj.group.id))

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

    return acl

def remove_none_from_dict(values):
    """Cleanup resolver input: remove keys with None values"""

    return {k:v for k,v in values.items() if v is not None}


def webpack_dev_server_is_available():
    """Return true when webpack developer server is available"""

    if settings.ENV == 'prod':
        return False

    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1.0)
            return s.connect_ex(('host.docker.internal', 9001)) == 0
        except Exception:
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


def send_mail_multi(subject, html_template, context, email_addresses, reply_to=None):
    if config.LANGUAGE:
        translation.activate(config.LANGUAGE)
    html_template = get_template(html_template)
    html_content = html_template.render(context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(subject, text_content, settings.FROM_EMAIL, email_addresses, reply_to=reply_to)
    email.attach_alternative(html_content, "text/html")
    return email


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


def get_base_url(context):
    return 'https://' + context.get_host()


def generate_code():
    return secrets.token_hex(10)

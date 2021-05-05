import logging
import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.db import connection
from tenants.models import Client
from blog.models import Blog
from core import config
from core.models import Comment, Entity
from discussion.models import Discussion
from flow.models import FlowId
from news.models import News
from question.models import Question

logger = logging.getLogger(__name__)

def object_handler(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    if (
        settings.IMPORTING
        or not config.FLOW_ENABLED
        or not created
        or instance.type_to_string not in config.FLOW_SUBTYPES
    ):
        return

    try:
        headers = {
            'Authorization': 'Token ' + config.FLOW_TOKEN,
            'Accept': 'application/json'
        }
        url = config.FLOW_APP_URL + 'api/cases/'

        tenant = Client.objects.get(schema_name=connection.schema_name)
        url_prefix = "https://" + tenant.domains.first().domain

        title = instance.title if instance.title else 'Geen titel gegeven'
        description = f"{instance.description} <br /><br /><a href='{url_prefix}{instance.url}'>{instance.url}</a>"

        json = {
            'casetype': str(config.FLOW_CASE_ID),
            'name': title,
            'description': description,
            'external_id': str(instance.id),
            'tags': []
        }

        r = requests.post(url, headers=headers, json=json)
        FlowId.objects.create(flow_id=r.json()['id'], object_id=instance.id)

    except Exception as e:
        logger.error("Error saving object on connected flow app: %s", e)


def comment_handler(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument

    if (
        settings.IMPORTING
        or not config.FLOW_ENABLED
        or not created
        or Entity.objects.get_subclass(id=instance.container.id).type_to_string not in config.FLOW_SUBTYPES
    ):
        return

    try:
        flow_id = str(FlowId.objects.get(object_id=instance.container.id).flow_id)
    except ObjectDoesNotExist:
        return

    try:
        headers = {
            'Authorization': 'Token ' + config.FLOW_TOKEN,
            'Accept': 'application/json'
        }
        url = config.FLOW_APP_URL + 'api/externalcomments/'

        json = {
            'case': flow_id,
            'author': instance.owner.name,
            'description': instance.description
        }

        requests.post(url, headers=headers, json=json)
    except Exception as e:
        logger.error("Error saving comment on connected flow app: %s", e)


post_save.connect(object_handler, sender=Blog)
post_save.connect(object_handler, sender=Discussion)
post_save.connect(object_handler, sender=News)
post_save.connect(object_handler, sender=Question)
post_save.connect(comment_handler, sender=Comment)

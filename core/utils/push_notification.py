
import json

from pywebpush import WebPushException, webpush
from django.conf import settings
from django.utils.translation import gettext as _
from core import config


def _process_subscription_info(subscription):

    return {
        "endpoint": subscription.endpoint,
        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}
    }


def send_web_push_notification(subscription, payload):
    subscription_data = _process_subscription_info(subscription)

    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_private_key = webpush_settings.get('VAPID_PRIVATE_KEY')
    vapid_admin_email = webpush_settings.get('VAPID_ADMIN_EMAIL')

    try:
        req = webpush(
            subscription_info=subscription_data,
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": "mailto:{}".format(vapid_admin_email)}
        )
        return req
    except WebPushException as e:
        # If the subscription is expired, delete it.
        if e.response.status_code == 410:
            subscription.delete()
        else:
            # Its other type of exception!
            raise e


def get_notification_payload(sender, verb, instance):
    if verb == 'created':
        return json.dumps({
            "head": _("New %(entity_type)s on %(site_name)s") % {'entity_type': instance.type_to_string, 'site_name': config.NAME},
            "body": _("%(sender_name)s created a %(entity_type)s: %(entity_title)s") % {'sender_name': sender.name, 'entity_type': instance.type_to_string, 'entity_title': instance.title},
            "icon": config.ICON,
            "url": instance.url
        })

    if verb == 'commented':
        return json.dumps({
            "head": _("New reaction on %(entity_type)s") % {'entity_type': instance.type_to_string},
            "body": _("%(sender_name)s posted a reaction on %(entity_title)s") % {'sender_name': sender.name, 'entity_title': instance.title},
            "icon": config.ICON,
            "url": instance.url
        })

    if verb == 'mentioned':
        return json.dumps({
            "head": _("New mention on %(entity_type)s") % {'entity_type': instance.type_to_string},
            "body": _("%(sender_name)s has mentioned you at %(entity_title)s") % {'sender_name': sender.name, 'entity_title': instance.title},
            "icon": config.ICON,
            "url": instance.url
        })

    return None

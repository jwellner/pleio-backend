# Create your tasks here
from __future__ import absolute_import, unicode_literals

import csv
import os
import json
import re
import signal_disabler
from email.utils import formataddr

from celery import shared_task
from celery.utils.log import get_task_logger

from django.core import management
from tenants.models import Client, Domain
from django_tenants.utils import schema_context
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Search
from core import config
from core.lib import html_to_text, access_id_to_acl
# from core.management.commands.send_notification_emails import get_notification
from core.models import ProfileField, UserProfileField, Entity, GroupMembership, Comment, Widget, Group
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation
from django.conf import settings
from notifications.signals import notify
from user.models import User
from django.utils.translation import ugettext_lazy
from elgg.models import GuidMap
from file.models import FileFolder

logger = get_task_logger(__name__)

@shared_task(bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    '''
    Dispatch period cron tasks for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Schedule cron %s for %s', period, client.schema_name)

        if period == 'hourly':
            send_notifications.delay(client.schema_name)

        if period in ['daily', 'weekly', 'monthly']:
            send_overview.delay(client.schema_name, period)

@shared_task(bind=True)
def dispatch_task(self, task, *kwargs):
    # pylint: disable=unused-argument
    '''
    Dispatch task for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Dispatch task %s for %s', task, client.schema_name)
        self.app.tasks[task].delay(client.schema_name, *kwargs)

@shared_task(bind=True)
def send_notifications(self, schema_name):
    # pylint: disable=unused-argument
    '''
    Send notification mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_notification_emails', '--schema', schema_name])

@shared_task(bind=True)
def send_overview(self, schema_name, period):
    # pylint: disable=unused-argument
    '''
    Send overview mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_overview_emails', '--schema', schema_name, '--interval', period])

@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild_all(self):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes and rebuild all tenants
    '''

    models = registry.get_models()

    # delete indexes
    for index in registry.get_indices(models):
        try:
            index.delete()
            logger.info('deleted index %s', index._name)
        except Exception:
            logger.info('index %s does not exist', index._name)

    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_rebuild.delay(client.schema_name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild(self, schema_name):
    # pylint: disable=unused-argument
    '''
    Rebuild search index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild \'%s\'', schema_name)

        models = registry.get_models()

        # create indexs if not exist
        for index in registry.get_indices(models):
            try:
                index.create()
                logger.info('created index %s')
            except Exception:
                logger.info('index %s already exists')

        # delete all objects for tenant before updating
        s = Search(index='_all').query().filter(
            'term', tenant_name=schema_name
        )

        logger.info('deleting %i objects', s.count())
        s.delete()

        for doc in registry.get_documents(models):
            logger.info("indexing %i '%s' objects",
                doc().get_queryset().count(),
                doc.django.model.__name__
            )
            qs = doc().get_indexing_queryset()
            doc().update(qs, parallel=False)

@shared_task(bind=True, ignore_result=True)
def elasticsearch_index_file(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    '''
    Index file for tenant
    '''
    with schema_context(schema_name):
        try:
            instance = FileFolder.objects.get(id=file_guid)
            registry.update(instance)
            registry.update_related(instance)

        except Exception as e:
            logger.error('elasticsearch_update %s %s: %s', schema_name, file_guid, e)


@shared_task(bind=True, ignore_result=True)
def send_mail_multi(self, schema_name, subject, html_template, context, email_address, reply_to=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    '''
    send email
    '''
    with schema_context(schema_name):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)
        html_template = get_template(html_template)
        html_content = html_template.render(context)
        text_content = html_to_text(html_content)

        from_mail = formataddr((config.NAME, settings.FROM_EMAIL))

        try:
            email = EmailMultiAlternatives(subject, text_content, from_mail, to=[email_address], reply_to=reply_to)
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            logger.error('email sent to %s failed. Error: %s', email_address, e)


def get_import_users_data(fields, row):
    data = {}
    for field in fields:
        field['value'] = row[field['csvColumn']]
        data[field['userField']] = field
    return data


def get_import_users_user(data):

    if 'id' in data:
        try:
            return User.objects.get(id=data['id']['value'])
        except Exception:
            pass
    if 'email' in data:
        try:
            return User.objects.get(email=data['email']['value'])
        except Exception:
            pass

    return False

@shared_task(bind=True, ignore_result=True)
def import_users(self, schema_name, fields, csv_location, performing_user_guid):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Import users
    '''
    with schema_context(schema_name):

        performing_user = User.objects.get(id=performing_user_guid)

        stats = {
            'created': 0,
            'updated': 0,
            'error': 0
        }

        logger.info("Start import on tenant %s by user", performing_user.email)

        success = False
        error_message = ''

        try:
            with open(csv_location) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    data = get_import_users_data(fields, row)
                    user = get_import_users_user(data)

                    if not user:
                        if 'name' in data and 'email' in data:
                            try:
                                user = User.objects.create(email=data['email']['value'], name=data['name']['value'])
                                stats['created'] += 1
                            except Exception:
                                stats['error'] += 1
                        else:
                            stats['error'] += 1
                    else:
                        stats['updated'] += 1

                    if user:
                        # create profile fields
                        for field, values in {d: data[d] for d in data if d not in ['id', 'email', 'name']}.items():

                            profile_field = ProfileField.objects.get(id=field)

                            if profile_field:
                                user_profile_field, created = UserProfileField.objects.get_or_create(
                                    profile_field=profile_field,
                                    user_profile=user.profile
                                )

                                user_profile_field.value = values['value']

                                if created:
                                    user_profile_field.read_access = access_id_to_acl(user, values['accessId'])
                                elif values['forceAccess']:
                                    user_profile_field.read_access = access_id_to_acl(user, values['accessId'])

                                user_profile_field.save()

            success = True

            os.remove(csv_location)

            logger.info("Import done with stats: %s ", stats)
        except Exception as e:
            error_message = "Import failed with message %s" % e
            logger.error(error_message)

        subject = ugettext_lazy("Import was a success") if success else ugettext_lazy("Import failed")
        template = "email/user_import_success.html" if success else "email/user_import_failed.html"

        tenant = Client.objects.get(schema_name=schema_name)
        context = {
            'site_name': config.NAME,
            'site_url': 'https://' + tenant.domains.first().domain,
            'primary_color': config.COLOR_PRIMARY,
            'user_name': performing_user.name,
            'stats_created': stats.get('created', 0),
            'stats_updated': stats.get('updated', 0),
            'stats_error': stats.get('error', 0),
            'error_message': error_message
        }

        send_mail_multi.delay(schema_name, subject, template, context, performing_user.email)

def get_notification_action_entity(notification):
    """ get entity from actoin_object_object_id """
    try:
        entity = Entity.objects.get_subclass(id=notification.action_object_object_id)
    except Exception:
        entity = User.objects.get(id=notification.actor_object_id)
        entity.group = None

    return entity


def get_notification(notification):
    """ get a mapped notification """
    entity = get_notification_action_entity(notification)
    performer = User.objects.get(id=notification.actor_object_id)
    entity_group = False
    entity_group_name = ""
    entity_group_url = ""
    if entity.group:
        entity_group = True
        entity_group_name = entity.group.name
        entity_group_url = entity.group.url

    return {
        'id': notification.id,
        'action': notification.verb,
        'performer_name': performer.name,
        'entity_title': entity.title,
        'entity_description': entity.description,
        'entity_group': entity_group,
        'entity_group_name': entity_group_name,
        'entity_group_url': entity_group_url,
        'entity_url': entity.url,
        'type_to_string': entity.type_to_string,
        'timeCreated': notification.timestamp,
        'isUnread': notification.unread
    }


@shared_task(bind=True, ignore_result=True)
def create_notification(self, schema_name, verb, entity_id, sender_id, recipient_ids):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    '''
    task for creating a notification. If the content of the notification is in a group and the recipient has configured direct notifications
    for this group. An email task wil be triggered with this notification
    '''
    with schema_context(schema_name):
        instance = Entity.objects.get_subclass(id=entity_id)
        sender = User.objects.get(id=sender_id)
        recipients = User.objects.filter(id__in=recipient_ids)

        # tuple with list is returned, get the notification created
        notifications = notify.send(sender, recipient=recipients, verb=verb, action_object=instance)[0][1]

        # only send direct notification for content in groups
        if instance.group:
            subject = ugettext_lazy("New notification at %(site_name)s: ") % {'site_name': config.NAME}
            tenant = Client.objects.get(schema_name=schema_name)
            site_url = "https://" + tenant.domains.first().domain
            site_name = config.NAME
            primary_color = config.COLOR_PRIMARY

            for notification in notifications:
                recipient = User.objects.get(id=notification.recipient_id)
                direct = False
                # get direct setting
                try:
                    direct = GroupMembership.objects.get(user=recipient, group=instance.group).notification_mode == 'direct'
                except Exception:
                    continue

                # send email direct and mark emailed as True
                if direct:
                    mapped_notifications = [get_notification(notification)]
                    user_url = site_url + '/user/' + recipient.guid + '/settings'
                    context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                                'notifications': mapped_notifications, 'show_excerpt': False}
                    send_mail_multi.delay(schema_name, subject, 'email/send_notification_emails.html', context, recipient.email)
                    notification.emailed = True
                    notification.save()


@shared_task(bind=True, ignore_result=True)
@signal_disabler.disable()
def replace_domain_links(self, schema_name, replace_domain=None, replace_elgg_id=False):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches


    '''
    Replace all links with old domain to new
    '''
    with schema_context(schema_name):
        # TODO: Disable updated_at

        tenant = Client.objects.get(schema_name=schema_name)
        tenant_domain = tenant.get_primary_domain().domain

        if not replace_domain:
            replace_domain = tenant_domain

        def _replace_links(text):
            if replace_elgg_id:
                # match links where old ID has to be replaced
                matches = re.findall(rf'(((https:\/\/{re.escape(replace_domain)})|(^|(?<=[ \"\n])))[\w\-\/]*\/(view|download)\/([0-9]+)[\w\-\.\/\?\%]*)', text)

                for match in matches:
                    link = match[0]
                    new_link = link
                    ids = re.findall(r'\/([0-9]+)', link)
                    for guid in ids:
                        map_entity = GuidMap.objects.filter(id=guid).first()
                        if map_entity:
                            new_link = new_link.replace(str(guid), str(map_entity.guid))

                    if link != new_link:
                        text = text.replace(link, new_link)

            # make absolute links relative
            text = text.replace(f"https://{replace_domain}/", f"/")

            # replace link without path
            text = text.replace(f"https://{replace_domain}", f"https://{tenant_domain}")
            return text

        def _replace_rich_description_json(rich_description):
            if rich_description:
                try:
                    data = json.loads(rich_description)
                    for idx in data["entityMap"]:
                        if data["entityMap"][idx]["type"] == "IMAGE":
                            data["entityMap"][idx]["data"]["src"] = _replace_links(data["entityMap"][idx]["data"]["src"])
                        if data["entityMap"][idx]["type"] in ["LINK", "DOCUMENT"]:
                            if "url" in data["entityMap"][idx]["data"]:
                                data["entityMap"][idx]["data"]["url"] = _replace_links(data["entityMap"][idx]["data"]["url"])
                            if "href" in data["entityMap"][idx]["data"]:
                                data["entityMap"][idx]["data"]["href"] = _replace_links(data["entityMap"][idx]["data"]["href"])
                    return json.dumps(data)
                except Exception:
                    pass
            return rich_description

        logger.info("Start replace links on %s from %s to %s", tenant, replace_domain, tenant_domain)

        # -- Replace MENU items
        menu_items = config.MENU
        for item in menu_items:
            if 'link' in item and item['link']:
                item['link'] = _replace_links(item['link'])

            for child in item.get("children", []):
                if 'link' in child and child['link']:
                    child['link'] = _replace_links(child['link'])

        config.MENU = menu_items

        # -- Replace DIRECT_LINKS
        direct_links = config.DIRECT_LINKS
        for item in direct_links:
            if 'link' in item and item['link']:
                item['link'] = _replace_links(item['link'])

        config.DIRECT_LINKS = direct_links

        # -- Replace entity descriptions
        entities = Entity.objects.all().select_subclasses()

        for entity in entities:
            if hasattr(entity, 'rich_description'):
                rich_description = _replace_rich_description_json(entity.rich_description)

                description = _replace_links(entity.description)

                if rich_description != entity.rich_description or description != entity.description:
                    entity.rich_description = rich_description
                    entity.description = description
                    entity.save()

        # -- Replace group description
        groups = Group.objects.all()

        for group in groups:
            rich_description = _replace_rich_description_json(group.rich_description)
            introduction = _replace_rich_description_json(group.introduction)
            welcome_message = _replace_rich_description_json(group.welcome_message)
            description = _replace_links(group.description)

            if rich_description != group.rich_description or \
                description != group.description or \
                introduction != group.introduction or \
                welcome_message != group.welcome_message:

                group.rich_description = rich_description
                group.description = description
                group.introduction = introduction
                group.welcome_message = welcome_message
                group.save()

        # -- Replace comment description
        comments = Comment.objects.all()

        for comment in comments:
            rich_description = _replace_rich_description_json(comment.rich_description)
            description = _replace_links(comment.description)

            if rich_description != comment.rich_description or description != comment.description:
                comment.rich_description = rich_description
                comment.description = description
                comment.save()

        # -- Replace widget settings
        widgets = Widget.objects.all()

        for widget in widgets:
            changed = False
            if widget.settings:
                for setting in widget.settings:
                    if 'value' in setting and isinstance(setting.get('value'), str):
                        new_value = _replace_links(setting.get('value'))
                        if new_value != setting.get('value'):
                            setting['value'] = new_value
                            changed = True

            if changed:
                widget.save()

    logger.info("Done replacing links")

@shared_task(bind=True)
def control_get_sites(self):
    # pylint: disable=unused-argument
    '''
    Used to sync sites to control
    '''
    clients = Client.objects.exclude(schema_name='public')

    sites = []
    for client in clients:
        sites.append({
            'id': client.id,
            'name': client.schema_name,
            'domain': client.get_primary_domain().domain
        })

    return sites

@shared_task(bind=True)
def control_add_site(self, schema_name, domain):
    # pylint: disable=unused-argument
    '''
    Create site from control
    '''
    with schema_context('public'):
        try:
            tenant = Client(schema_name=schema_name, name=schema_name)
            tenant.save()

            d = Domain()
            d.domain = domain
            d.tenant = tenant
            d.is_primary = True
            d.save()
        except Exception as e:
            raise Exception(e)

        return tenant.id

@shared_task(bind=True)
def control_delete_site(self, site_id):
    # pylint: disable=unused-argument
    '''
    Delete site from control
    '''
    with schema_context('public'):
        try:
            tenant = Client.objects.get(id=site_id)
            # tenant.auto_drop_schema = True 
            tenant.delete()
        except Exception as e:
            # raise general exception because remote doenst have Client exception
            raise Exception(e)

    return True
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
from tenants.models import Client
from django_tenants.utils import schema_context
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Search
from core import config
from core.lib import html_to_text, access_id_to_acl, get_model_by_subtype, map_notification, tenant_schema, get_default_email_context
from core.models import ProfileField, UserProfileField, Entity, GroupMembership, Comment, Widget, Group, NotificationMixin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import timezone, translation
from django.conf import settings
from notifications.signals import notify
from notifications.models import Notification
from user.models import User
from django.utils.translation import ugettext_lazy
from elgg.models import GuidMap
from file.models import FileFolder

logger = get_task_logger(__name__)

@shared_task()
def create_notifications_for_scheduled_content(schema_name):
    with schema_context(schema_name):

        for instance in Entity.objects.filter(notifications_created=False, published__lte=timezone.now()).exclude(published=None).select_subclasses():
            # instance has no NotificationMixin impemented. Set notifications_created True so it is skipped next time.
            if instance.__class__ not in NotificationMixin.__subclasses__():
                instance.notifications_created = True
                instance.save()
                continue

            # instance has no group. Set notifications_created True so it is skipped next time.
            if not instance.group:
                instance.notifications_created = True
                instance.save()
                continue

            # there are already notifications for this instance.id. Set notifications_created True so it is skipped next time.
            if Notification.objects.filter(action_object_object_id=instance.id).count() > 0:
                instance.notifications_created = True
                instance.save()
                continue

            create_notification.delay(tenant_schema(), 'created', instance.id, instance.owner.id)


@shared_task(bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    '''
    Dispatch period cron tasks for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Schedule cron %s for %s', period, client.schema_name)

        if period == 'hourly':
            create_notifications_for_scheduled_content(client.schema_name)
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
def elasticsearch_recreate_indices(self, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes, creates indexes
    '''
    if index_name:
        models = [get_model_by_subtype(index_name)]
    else:
        models = registry.get_models()

    # delete indexes
    for index in registry.get_indices(models):
        try:
            index.delete()
            logger.info('deleted index %s', index._name)
        except Exception:
            logger.info('index %s does not exist', index._name)

        try:
            index.create()
            logger.info('created index %s')
        except Exception:
            logger.info('index %s already exists')


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild_all(self, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes, creates indexes and populate tenants

    No option passed then all indices are rebuild
    Options: ['news', 'file', 'question' 'wiki', 'discussion', 'page', 'event', 'blog', 'user', 'group']

    '''
    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_rebuild.delay(client.schema_name, index_name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild(self, schema_name, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access    
    '''
    Rebuild search index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild \'%s\'', schema_name)

        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()

        for index in registry.get_indices(models):
            elasticsearch_repopulate_index_for_tenant.delay(schema_name, index._name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_repopulate_index_for_tenant(self, schema_name, index_name):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild index for tenant
    '''
    with schema_context(schema_name):
        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()


        for index in registry.get_indices(models):          
            logger.info('elasticsearch_repopulate_index_for_tenant \'%s\' \'%s\'', index_name, schema_name)

            # delete all objects for tenant before updating
            s = Search(index=index._name).query().filter(
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

                if doc.django.model.__name__ == 'FileFolder':
                    doc().update(qs, parallel=False, chunk_size=10)
                else:
                    doc().update(qs, parallel=False, chunk_size=500)


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
def send_mail_multi(self, schema_name, subject, html_template, context, email_address, reply_to=None, language=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    '''
    send email
    '''
    with schema_context(schema_name):
        if language:
            translation.activate(language)
        else:
            translation.activate(config.LANGUAGE)

        if not User.objects.filter(is_active=False, email=email_address).first():
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


@shared_task(bind=True, ignore_result=True)
def import_users(self, schema_name, fields, csv_location, performing_user_guid):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Import users
    '''

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

    with schema_context(schema_name):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)

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
            'header_color': config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY,
            'user_name': performing_user.name,
            'stats_created': stats.get('created', 0),
            'stats_updated': stats.get('updated', 0),
            'stats_error': stats.get('error', 0),
            'error_message': error_message
        }

        send_mail_multi.delay(schema_name, subject, template, context, performing_user.email)

@shared_task(bind=True, ignore_result=True)
def create_notification(self, schema_name, verb, entity_id, sender_id):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    '''
    task for creating a notification. If the content of the notification is in a group and the recipient has configured direct notifications
    for this group. An email task wil be triggered with this notification
    '''
    with schema_context(schema_name):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)
        
        instance = Entity.objects.get_subclass(id=entity_id)
        sender = User.objects.get(id=sender_id)

        if verb == "created":
            recipients = []
            if instance.group:
                for member in instance.group.members.filter(type__in=['admin', 'owner', 'member']).exclude(notification_mode='disable'):
                    if sender == member.user:
                        continue
                    if not instance.can_read(member.user):
                        continue
                    recipients.append(member.user)
        elif verb == "commented":
            recipients = []
            if hasattr(instance, 'followers'):
                for follower in instance.followers():
                    if sender == follower:
                        continue
                    if not instance.can_read(follower):
                        continue
                    recipients.append(follower)
        else:
            return

        # tuple with list is returned, get the notification created
        notifications = notify.send(sender, recipient=recipients, verb=verb, action_object=instance)[0][1]

        instance.notifications_created = True
        instance.save()

        # only send direct notification for content in groups
        if instance.group:
            subject = ugettext_lazy("New notification at %(site_name)s: ") % {'site_name': config.NAME}

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
                    # do not send mail when notifications are disabled, but mark as send (so when enabled you dont receive old notifications!)
                    if recipient.profile.receive_notification_email:
                        context = get_default_email_context(recipient)
                        context['show_excerpt'] = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
                        context['notifications'] = [map_notification(notification)]

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
                # match links where old ID has to be simply replaced
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

                # match thumbnail links and replace with file download link
                matches = re.findall(
                    rf'(((https:\/\/{re.escape(replace_domain)})|(^|(?<=[ \"\n])))\/mod\/file\/thumbnail.php\?file_guid=([0-9]+)[^\"^ ]*)',
                    text
                )

                for match in matches:
                    link = match[0]
                    file_id = match[4]
                    has_file = GuidMap.objects.filter(id=file_id, object_type="file").first()
                    if has_file:
                        try:
                            file_entity = FileFolder.objects.get(id=has_file.guid)
                            text = text.replace(link, file_entity.download_url)
                        except Exception:
                            pass


                # match old /file/view links and replace with new /files/view link, only for migrates files
                matches = re.findall(
                    rf'(((https:\/\/{re.escape(replace_domain)})|(^|(?<=[ \"\n])))\/file\/view\/([\w\-]+)\/[\w\-\.\/\?\%]*)',
                    text
                )

                for match in matches:
                    link = match[0]
                    file_id = match[4]

                    # try old elgg id
                    try:
                        has_file = GuidMap.objects.filter(id=file_id, object_type="file").first()
                        if has_file:
                            file_entity = FileFolder.objects.get(id=has_file.guid)
                            text = text.replace(link, file_entity.url)
                    except Exception:
                        pass

                    # try new uuid
                    try:
                        has_file = GuidMap.objects.filter(guid=file_id, object_type="file").first()
                        if has_file:
                            file_entity = FileFolder.objects.get(id=file_id)
                            text = text.replace(link, file_entity.url)
                    except Exception:
                        pass

                # match group profile links and replace new link
                matches = re.findall(
                    rf'(((https:\/\/{re.escape(replace_domain)})|(^|(?<=[ \"\n])))\/groups\/profile\/([0-9]+)\/[^\"^ ]*)',
                    text
                )

                for match in matches:
                    link = match[0]
                    group_id = match[4]
                    has_group = GuidMap.objects.filter(id=group_id, object_type="group").first()

                    if has_group:
                        try:
                            group_entity = Group.objects.get(id=has_group.guid)
                            text = text.replace(link, group_entity.url)
                        except Exception:
                            pass

                # match and replace folder links
                matches = re.findall(
                    rf'(((https:\/\/{re.escape(replace_domain)})|(^|(?<=[ \"\n])))\/file\/group\/([0-9]+)\/all(#([0-9]+))?[^\"^ ]*)',
                    text
                )

                for match in matches:
                    link = match[0]
                    group_id = match[4]
                    folder_id = match[6]
                    has_folder = GuidMap.objects.filter(id=folder_id, object_type="folder").first() if folder_id else False
                    has_group = GuidMap.objects.filter(id=group_id, object_type="group").first()


                    if has_folder:
                        try:
                            folder_entity = FileFolder.objects.get(id=has_folder.guid)
                            text = text.replace(link, folder_entity.url)
                        except Exception:
                            pass
                    elif has_group:
                        try:
                            group_entity = Group.objects.get(id=has_group.guid)
                            text = text.replace(link, group_entity.url + "/files")
                        except Exception:
                            pass


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

        # -- Replace REDIRECTS items
        redirects = {}
        for k, v in config.REDIRECTS.items():
            redirects[k] = _replace_links(v)

        config.REDIRECTS = redirects

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
            description = _replace_links(group.description)

            try:
                introduction = json.loads(group.introduction)
                introduction = _replace_rich_description_json(group.introduction)
            except Exception:
                # old elgg sites dont have draftjs json
                introduction = _replace_links(group.description)

            try:
                welcome_message = json.loads(group.welcome_message)
                welcome_message = _replace_rich_description_json(group.welcome_message)
            except Exception:
                # old elgg sites dont have draftjs json
                welcome_message = _replace_links(group.welcome_message)

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

import csv
import os
import re
import signal_disabler

from celery import shared_task
from celery.utils.log import get_task_logger
from core import config
from core.lib import access_id_to_acl
from core.tasks.mail_tasks import send_mail_multi
from core.models import Group, Entity, Widget, Comment, ProfileField, UserProfileField
from django.core import management
from django.utils import translation
from django.utils.translation import ugettext_lazy
from django_tenants.utils import schema_context
from elgg.models import GuidMap
from file.models import FileFolder
from tenants.models import Client
from user.models import User

logger = get_task_logger(__name__)

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
                rich_description = _replace_links(entity.rich_description)

                if rich_description != entity.rich_description:
                    entity.rich_description = rich_description
                    entity.save()

        # -- Replace group description
        groups = Group.objects.all()

        for group in groups:
            rich_description = _replace_links(group.rich_description)
            introduction = _replace_links(group.description)
            welcome_message = _replace_links(group.welcome_message)

            if rich_description != group.rich_description or \
                introduction != group.introduction or \
                welcome_message != group.welcome_message:

                group.rich_description = rich_description
                group.introduction = introduction
                group.welcome_message = welcome_message
                group.save()

        # -- Replace comment description
        comments = Comment.objects.all()

        for comment in comments:
            rich_description = _replace_links(comment.rich_description)

            if rich_description != comment.rich_description:
                comment.rich_description = rich_description
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
def draft_to_tiptap(self, schema_name):
    # pylint: disable=unused-argument
    '''
    Send overview mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'draft_to_tiptap', '--schema', schema_name])

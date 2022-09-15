import csv
import os
import signal_disabler
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from celery import shared_task
from celery.utils.log import get_task_logger
from core import config
from core.lib import access_id_to_acl
from core.tasks.mail_tasks import send_mail_multi
from core.models import Group, Entity, Widget, Comment, ProfileField, UserProfileField, ResizedImage
from django.utils import translation
from django.utils.translation import ugettext_lazy
from django_tenants.utils import schema_context
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
            'error': 0,
            'processed': 0,
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

                    stats['processed'] += 1

                    if stats['processed'] % 100 == 0:
                        logger.info('Batch users imported: %s', stats)

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
def replace_domain_links(self, schema_name, replace_domain=None):
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
            introduction = _replace_links(group.introduction)
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
def image_resize(self, schema_name, resize_image_id):
    # pylint: disable=unused-argument
    with schema_context(schema_name):
        try:
            resized_image = ResizedImage.objects.get(id=resize_image_id)
        except Exception as e:
            logger.error(e)
            return

        if resized_image.status == ResizedImage.OK:
            return

        try:
            infile = resized_image.original.upload_field.open()
            im = Image.open(infile)

            # Set the smallest dimension to the requested size to avoid pixelly images
            if im.width > im.height:
                thumbnail_size = (im.width, resized_image.size)
            else:
                thumbnail_size = (resized_image.size, im.height)

            im.thumbnail(thumbnail_size, Image.LANCZOS)
            output = BytesIO()
            im.save(output, im.format)
            contents = output.getvalue()

            resized_image.mime_type = Image.MIME[im.format]
            resized_image.upload.save(resized_image.original.upload_field.name, ContentFile(contents))
            resized_image.status = ResizedImage.OK
            resized_image.save()

        except Exception as e:
            resized_image.status = ResizedImage.FAILED
            resized_image.message = str(e)
            resized_image.save()
            logger.error(e)

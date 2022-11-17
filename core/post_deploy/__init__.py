import csv
import json
import os
from collections import defaultdict

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Prefetch, F
from django.utils.translation import gettext, activate
from post_deploy import post_deploy_action

from concierge.api import fetch_avatar
from core import config
from core.constances import ACCESS_TYPE
from core.elasticsearch import schedule_index_document
from core.lib import tenant_schema, is_schema_public, get_full_url
from core.models import Group, Entity, Revision, Widget
from core.models.attachment import Attachment
from core.tasks import strip_exif_from_file
from core.utils.entity import load_entity_by_id
from core.utils.migrations import category_tags
from user.models import User
from notifications.models import Notification

from .restore_tag_categories import restore_tag_categories

logger = get_task_logger(__name__)


@post_deploy_action
def schedule_index_users():
    if is_schema_public():
        return

    for user in User.objects.filter(is_active=True):
        schedule_index_document(user)


@post_deploy_action
def sync_is_submit_updates_enabled_group_setting():
    """
    Copy the site setting for submit-updates in groups into the group setting.
    """
    if is_schema_public():
        return

    site_setting = config.STATUS_UPDATE_GROUPS
    for group in Group.objects.all():
        group.is_submit_updates_enabled = site_setting
        group.save()


@post_deploy_action
def fix_write_access_for_several_entity_types():
    if is_schema_public():
        return

    for pk, write_access, owner, in Entity.objects.all().values_list('id', 'write_access', 'owner'):
        if len(write_access) == 0:
            entity = load_entity_by_id(pk, [Entity])
            entity.write_access = [ACCESS_TYPE.user.format(owner)]
            entity.save()


@post_deploy_action(auto=False)
def remove_notifications_with_broken_relation():
    if is_schema_public():
        return

    count = 0

    queryset = Notification.objects.prefetch_related(Prefetch('action_object'))

    for notification in queryset.iterator(chunk_size=10000):  # using iterator for large datasets memory consumption
        if not notification.action_object:
            notification.delete()
            count += 1

    logger.info("Deleted %s broken notifications", count)


@post_deploy_action
def create_initial_revisions():
    if is_schema_public():
        return

    activate(config.LANGUAGE)
    Revision.objects.all().delete()
    for entity in Entity.objects.select_subclasses():
        if entity.has_revisions():
            try:
                revision = Revision()
                revision.store_initial_version(entity)
                revision.description = gettext("Automatically generated initial revision")
                revision.save()
            except Exception:
                pass


@post_deploy_action
def create_initial_revisions_for_left_over_entities():
    if is_schema_public():
        return

    activate(config.LANGUAGE)
    for entity in Entity.objects.select_subclasses():
        if entity.has_revisions() and not Revision.objects.filter(_container=entity).exists():
            try:
                revision = Revision()
                revision.store_initial_version(entity)
                revision.description = gettext("Automatically generated initial revision")
                revision.save()
            except Exception:
                pass


@post_deploy_action
def migrate_widgets_that_have_sorting_enabled():
    if is_schema_public():
        return

    for record in Widget.objects.all():
        _update_widget(record)


def _update_widget(record):
    try:
        new_settings = []
        for setting in record.settings:
            if setting['key'] == 'sortingEnabled':
                setting['key'] = 'sortingOptions'
                setting['value'] = json.dumps(["timePublished", "lastAction"] if setting['value'] == '1' else [])
            new_settings.append(setting)
        record.settings = new_settings
        record.save()
    except Exception:
        pass


@post_deploy_action
def migrate_entities():
    if is_schema_public():
        return

    Entity.objects.filter(last_action__isnull=False,
                          published__gt=F('last_action')).update(last_action=F('published'))


# no more exectute this method
# @post_deploy_action(auto=False)
def strip_article_images_of_exif_data():
    # pylint: disable=no-value-for-parameter
    if is_schema_public():
        return

    # pylint: disable=unreachable
    for attachment_guid in Attachment.objects.all().values_list('id', flat=True):
        strip_exif_from_file.delay(schema=tenant_schema(),
                                   attachment_guid=str(attachment_guid))

    for entity in Entity.objects.all().select_subclasses():
        if hasattr(entity, 'featured_image') and entity.featured_image:
            strip_exif_from_file(schema=tenant_schema(), file_folder_guid=entity.featured_image.guid)


# no more exectute this method
# @post_deploy_action
def migrate_categories():
    if is_schema_public():
        return

    try:
        category_tags.WidgetMigration().run()
        category_tags.UserMigration().run()
        category_tags.GroupMigration().run()
        category_tags.EntityMigration().run()
        category_tags.cleanup()
    except Exception as e:
        logger.error("migrate_categories@%s: %s (%s)", tenant_schema(), str(e), str(e.__class__))
        raise


# no more exectute this method
# @post_deploy_action
def migrate_widgets_for_match_strategy():
    if is_schema_public():
        return

    for widget in Widget.objects.all():
        if widget.type != 'objects':
            continue

        if 'matchStrategy' in [s.get('key') for s in widget.settings]:
            continue

        widget.settings.append({
            'key': 'matchStrategy',
            'value': 'all'
        })
        widget.save()


@post_deploy_action
def add_admin_weight_to_group_membership_objects():
    if is_schema_public():
        return

    from core.models import GroupMembership
    GroupMembership.objects.all().update(admin_weight=3)
    GroupMembership.objects.filter(type='owner').update(admin_weight=1)
    GroupMembership.objects.filter(type='admin').update(admin_weight=2)


@post_deploy_action(auto=False)
def verify_user_account_avatars():
    if is_schema_public():
        return

    for user in User.objects.filter(is_active=True):
        try:
            if user.picture:
                response = requests.get(user.picture, timeout=10)
                if response.status_code == 404:
                    result = fetch_avatar(user)
                    if result.get('originalAvatarUrl') is None:
                        user.profile.picture_file = None
                        user.profile.save()
                        user.picture = None
                        user.save()
                    else:
                        user.picture = result.get('avatarUrl')
                        user.save()
        except Exception as e:
            logger.error(str(e))
            logger.error(str(e.__class__))


@post_deploy_action
def write_missing_file_report():
    if is_schema_public():
        return

    from file.models import FileFolder
    report_file = os.path.join(settings.BACKUP_PATH, "missing_file_report_" + tenant_schema()) + '.csv'
    total = 0
    files_ok = 0
    files_err = 0
    with open(report_file, 'w') as fh:
        writer = csv.writer(fh, delimiter=';')
        writer.writerow(['id', 'path', 'url', 'name', 'owner', 'group', 'groupowner', 'groupownermail'])
        for file in FileFolder.objects.filter(type=FileFolder.Types.FILE, upload__isnull=False):
            try:
                if not os.path.exists(file.upload.path):
                    writer.writerow([
                        file.guid,
                        file.upload.path,
                        get_full_url(file.url),
                        file.title,
                        file.owner.name if file.owner else '-',
                        file.group.name if file.group else '-',
                        file.group.owner.name if file.group else '-',
                        file.group.owner.email if file.group else '-',
                    ])
                    total += 1
                else:
                    files_ok += 1
            except Exception as e:
                writer.writerow([
                    file.guid,
                    f"Error: {e.__class__} {e}",
                    file.owner.name if file.owner else '',
                    file.group.name if file.group else '',
                    file.group.owner.name if file.group else '',
                    file.group.owner.email if file.group else '',
                ])
                total += 1
                files_err += 1
        writer.writerow([f"{total} files can't be found on the disk."])
        writer.writerow([f"{files_ok} files were just fine."])
        writer.writerow([f"{files_err} files had errors while checking."])

    if total == 0:
        os.unlink(report_file)


@post_deploy_action
def no_operation():
    logger.info("running core.post_deploy.no_operation at %s", tenant_schema())

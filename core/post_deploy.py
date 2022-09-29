import logging
import json

from django.utils.translation import gettext, activate
from post_deploy import post_deploy_action

from core import config
from core.constances import ACCESS_TYPE
from core.elasticsearch import schedule_index_document
from core.lib import is_schema_public
from core.models import Group, Entity, Revision, Widget
from core.utils.entity import load_entity_by_id
from user.models import User
from notifications.models import Notification
from django.db.models import Prefetch, F

LOGGER = logging.getLogger(__name__)


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

    LOGGER.info("Deleted %s broken notifications", count)


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

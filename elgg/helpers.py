import os
from datetime import datetime
from phpserialize import unserialize

from cms.models import Page
from user.models import User
from file.models import FileFolder
from core.lib import ACCESS_TYPE, access_id_to_acl
from elgg.models import (
    ElggEntities, ElggObjectsEntity, ElggPrivateSettings, ElggConfig, GuidMap, ElggEntityViews, ElggEntityViewsLog
)
from core.models import EntityView, EntityViewCount

# TODO: How to implement everywhere ?
def get_guid(guid):
    try:
        return GuidMap.objects.get(id=guid).guid
    except Exception:
        return guid

class ElggHelpers():
    database = None

    def __init__(self, database):
        self.database = database

    def get_list_values(self, value):
        if not value:
            return []
        return value if isinstance(value, list) else [value]

    def get_plugin_setting(self, setting, plugin="pleio_template"):
        try:
            plugin = ElggObjectsEntity.objects.using(self.database).get(entity__subtype__subtype='plugin', title=plugin)
        except Exception:
            print(f"Plugin {plugin} not found")
            return None

        try:
            setting = ElggPrivateSettings.objects.using(self.database).get(entity__guid=plugin.entity.guid, name=setting)
        except Exception:
            print(f"Setting {setting} for {plugin} not found")
            return None

        return setting.value

    def get_site_config(self, name):
        try:
            config = ElggConfig.objects.using(self.database).get(name=name)
        except Exception:
            print(f"Site config {name} not found")
            return None

        value = bytes(config.value.encode())
        return unserialize(value, decode_strings=True)

    def get_profile_field_type(self, name):
        profile_field_entity = ElggEntities.objects.using(self.database).filter(
            subtype__subtype="custom_profile_field",
            metadata__value__string=name,
            metadata__name__string="metadata_name").first()

        if not profile_field_entity:
            return 'textField'

        metadata_type = profile_field_entity.metadata.filter(name__string="metadata_type").first()

        elgg_type = metadata_type.value.string if metadata_type else None

        if elgg_type in ['dropdown', 'radio', 'pm_rating']:
            field_type = 'selectField'
        elif elgg_type in ['date', 'birthday', 'calendar', 'pm_datepicker']:
            field_type = 'dateField'
        elif elgg_type in ['longtext']:
            field_type = 'htmlField'
        elif elgg_type in ['multiselect']:
            field_type = 'multiSelectField'
        else:
            field_type = 'textField'

        return field_type

    def get_profile_category(self, name):
        profile_field_entity = ElggEntities.objects.using(self.database).filter(
            subtype__subtype="custom_profile_field",
            metadata__value__string=name,
            metadata__name__string="metadata_name").first()

        if not profile_field_entity:
            return None

        metadata_type = profile_field_entity.metadata.filter(name__string="metadata_label").first()

        category = metadata_type.value.string if metadata_type else None
        return category

    def get_profile_options(self, name):
        profile_field_entity = ElggEntities.objects.using(self.database).filter(
            subtype__subtype="custom_profile_field",
            metadata__value__string=name,
            metadata__name__string="metadata_name").first()

        if not profile_field_entity:
            return []

        metadata_type = profile_field_entity.metadata.filter(name__string="metadata_options").first()

        options = metadata_type.value.string.split(',') if metadata_type else []
        return options

    def get_profile_is_editable(self, name):
        profile_field_entity = ElggEntities.objects.using(self.database).filter(
            subtype__subtype="custom_profile_field",
            metadata__value__string=name,
            metadata__name__string="metadata_name").first()

        if not profile_field_entity:
            return True

        metadata_type = profile_field_entity.metadata.filter(name__string="user_editable").first()

        editable = metadata_type.value.string == 'yes' if metadata_type else True # default True
        return editable

    def get_menu(self, menu_input):

        menu = []

        for item in menu_input:
            if 'children' not in item:
                item["children"] = []
            menu.append(item)

        return menu

    def save_best_answer(self, question, comment, elgg_entity):
        if elgg_entity.relation.filter(relationship="correctAnswer", left__guid=elgg_entity.guid).first():
            question.best_answer = comment
            question.save()

    def save_parent_page(self, elgg_page):
        guid_map_page = GuidMap.objects.get(id=elgg_page.entity.guid, object_type='page')
        page = Page.objects.get(id=guid_map_page.guid)

        try:

            guid_map_parent = GuidMap.objects.get(id=elgg_page.entity.container_guid, object_type='page')
            parent = Page.objects.get(id=guid_map_parent.guid)
            page.parent = parent
            page.save()

        except Exception:
            pass


    def save_parent_folder(self, elgg_folder):
        guid_map_folder = GuidMap.objects.get(id=elgg_folder.entity.guid, object_type='folder')
        folder = FileFolder.objects.get(id=guid_map_folder.guid)

        try:
            parent_id = elgg_folder.entity.get_metadata_value_by_name("parent_guid")
            if parent_id:
                guid_map_parent = GuidMap.objects.get(id=parent_id, object_type='folder')
                parent_folder = FileFolder.objects.get(id=guid_map_parent.guid)
                folder.parent = parent_folder
                folder.save()

        except Exception:
            pass

    def get_elgg_file_path(self, elgg_file):
        filename = elgg_file.entity.get_metadata_value_by_name("filename")

        user_guid = GuidMap.objects.get(id=elgg_file.entity.owner_guid, object_type='user').guid
        user = User.objects.get(id=user_guid)

        dt_user = user.created_at
        year = dt_user.strftime('%Y')
        month = dt_user.strftime('%m')
        day = dt_user.strftime('%d')
        file_path = os.path.join(
            "migrated", year, month, day, str(elgg_file.entity.owner_guid), filename
        )
        return file_path

    def save_and_get_featured_image(self, elgg_entity):

        try:
            time_created = datetime.fromtimestamp(elgg_entity.entity.time_created)
            year = time_created.strftime('%Y')
            month = time_created.strftime('%m')
            day = time_created.strftime('%d')

            filename = "%s.jpg" % (str(elgg_entity.entity.guid))

            file_path = os.path.join(
                "migrated", year, month, day, str(elgg_entity.entity.guid), 'featured', filename
            )

            # Featured images do not have a file entity
            entity = FileFolder()

            entity.mime_type = "image/jpeg"
            entity.title = ""
            entity.upload.name = file_path

            entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

            entity.is_folder = False

            entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
            entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

            entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
            entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

            entity.save()
            return entity
        except Exception:
            return None

    def save_and_get_group_icon(self, elgg_entity):

        # TODO: maybe group icon will be saved as a FileFolde in the future
        try:
            group_owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

            time_created = group_owner.created_at
            year = time_created.strftime('%Y')
            month = time_created.strftime('%m')
            day = time_created.strftime('%d')

            filename = "%slarge.jpg" % (str(elgg_entity.entity.guid))

            file_path = os.path.join(
                "migrated", year, month, day, str(elgg_entity.entity.owner_guid), 'groups', filename
            )

            # Group icons do not have a file entity
            entity = FileFolder()

            entity.mime_type = "image/jpeg"
            entity.title = ""
            entity.upload.name = file_path

            entity.owner = group_owner

            entity.is_folder = False

            entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
            entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

            entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
            entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

            entity.save()

            return entity.url

        except Exception:
            return ""

    def save_and_get_site_logo_or_icon(self, elgg_site, image_type):

        try:
            time_created = datetime.fromtimestamp(elgg_site.entity.time_created)
            year = time_created.strftime('%Y')
            month = time_created.strftime('%m')
            day = time_created.strftime('%d')

            if elgg_site.entity.get_metadata_value_by_name(image_type + "_extension"):
                extension = elgg_site.entity.get_metadata_value_by_name(image_type + "_extension")
            else:
                extension = 'jpg'

            if extension == 'svg':
                mime_type = 'image/svg+xml'
            elif extension == 'png':
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            filename = "%s_%s.%s" % (str(elgg_site.entity.guid), image_type, extension)

            file_path = os.path.join(
                "migrated", year, month, day, str(elgg_site.entity.guid), 'pleio_template/', filename
            )

            entity = FileFolder()

            entity.owner = User.objects.filter(is_admin=True).first()

            entity.upload.name = file_path
            entity.mime_type = mime_type

            entity.read_access = access_id_to_acl(entity, 2)
            entity.write_access = access_id_to_acl(entity, 0)

            entity.save()

            url = "/site/%s/%s" % (image_type, str(entity.id))
            return url
        except Exception:
            return ""

    def save_entity_annotations(self, elgg_entity, entity, annotation_types=['vote', 'bookmark', 'follow', 'view_count', 'views']):
        # pylint: disable=dangerous-default-value
        # pylint: disable=too-many-locals
        if "vote" in annotation_types:
            annotations = elgg_entity.entity.annotation.filter(name__string="vote", value__string="1")
            for vote in annotations:
                user = User.objects.get(id=GuidMap.objects.get(id=vote.owner_guid, object_type="user").guid)
                entity.add_vote(user, 1)
        if "bookmark" in annotation_types:
            bookmarks = elgg_entity.entity.relation_inverse.filter(relationship="bookmarked", right__guid=elgg_entity.entity.guid)
            for bookmark in bookmarks:
                user = User.objects.get(id=GuidMap.objects.get(id=bookmark.left.guid, object_type="user").guid)
                entity.add_bookmark(user)
        if "follow" in annotation_types:
            follows = elgg_entity.entity.relation_inverse.filter(relationship="content_subscription", right__guid=elgg_entity.entity.guid)
            for follow in follows:
                user = User.objects.get(id=GuidMap.objects.get(id=follow.left.guid, object_type="user").guid)
                entity.add_follow(user)
        if "view_count" in annotation_types:
            view_count = ElggEntityViews.objects.using(self.database).filter(guid=elgg_entity.entity.guid).first()
            if view_count:
                EntityViewCount.objects.create(entity=entity, views=view_count.views)
        if "views" in annotation_types:
            user_ids = list(ElggEntityViewsLog.objects.using(self.database).filter(
                entity_guid=elgg_entity.entity.guid).values_list('performed_by_guid', flat=True)
            )
            user_guids = list(GuidMap.objects.filter(id__in=user_ids, object_type="user").values_list('guid', flat=True))
            users = User.objects.filter(id__in=user_guids)
            if users:
                for user in users:
                    EntityView.objects.create(entity=entity, viewer=user)

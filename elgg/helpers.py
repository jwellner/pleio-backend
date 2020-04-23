import os
from datetime import datetime
from phpserialize import unserialize
from elgg.models import ElggEntities, ElggObjectsEntity, ElggPrivateSettings, ElggConfig, GuidMap
from cms.models import Page
from user.models import User
from file.models import FileFolder
from core.lib import ACCESS_TYPE, access_id_to_acl

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

from phpserialize import unserialize
from elgg.models import ElggEntities, ElggObjectsEntity, ElggPrivateSettings, ElggConfig

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

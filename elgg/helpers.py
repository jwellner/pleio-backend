import os
from datetime import datetime
from django.core.files.storage import default_storage
from phpserialize import unserialize

from cms.models import Page
from user.models import User
from file.models import FileFolder
from wiki.models import Wiki
from core.lib import access_id_to_acl, is_valid_url_or_path
from elgg.models import (
    ElggEntities, ElggObjectsEntity, ElggPrivateSettings, ElggConfig, GuidMap, ElggEntityViews,
    ElggEntityViewsLog, ElggAccessCollections, ElggEntityRelationships
)
from core.models import EntityView, EntityViewCount, ProfileField


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

    def is_plugin_active(self, plugin_name):
        try:
            plugin = ElggObjectsEntity.objects.using(self.database).get(entity__subtype__subtype='plugin', title=plugin_name)
        except Exception:
            print(f"Plugin {plugin} not found")
            return None

        try:
            ElggEntityRelationships.objects.using(self.database).get(left=plugin.entity.guid, relationship='active_plugin')
            return True
        except Exception:
            # plugin not active
            return False


    def get_site_config(self, name):
        try:
            config = ElggConfig.objects.using(self.database).get(name=name)
        except Exception:
            print(f"Site config {name} not found")
            return None

        value = bytes(config.value.encode())
        return unserialize(value, decode_strings=True)

    def get_rewrites(self):
        # pylint: disable=unused-variable
        rewrites_serialized = self.get_plugin_setting("rewrites", "rewrite")

        if rewrites_serialized:
            value = unserialize(bytes(rewrites_serialized.encode()), decode_strings=True)
            rewrites = {}
            rewrites_count = 0

            for k, v in value.items():
                source = v['source']
                if not source.startswith('/'):
                    source = '/' + source
                destination = v['destination']
                if not destination.startswith('/') and not destination.startswith('http'):
                    destination = '/' + destination

                if not is_valid_url_or_path(source) or is_valid_url_or_path(destination):
                    continue

                # skip if rewrite source already exists
                try:
                    rewrites[source] = destination
                    rewrites_count = rewrites_count + 1
                except Exception:
                    pass
            print(f"{rewrites_count} rewrites saved")
            return rewrites
        return {}


    def get_profile_field(self, name):
        profile_field_entities = ElggEntities.objects.using(self.database).filter(
            subtype__subtype="custom_profile_field"
        )

        for item in profile_field_entities:
            if item.get_metadata_value_by_name('metadata_name') == name:
                return item

        return None

    def get_profile_field_type(self, name):

        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return 'text_field'

        metadata_type = profile_field_entity.metadata.filter(name__string="metadata_type").first()

        elgg_type = metadata_type.value.string if metadata_type else None

        if elgg_type in ['dropdown', 'radio', 'pm_rating']:
            field_type = 'select_field'
        elif elgg_type in ['date', 'birthday', 'calendar', 'pm_datepicker']:
            field_type = 'date_field'
        elif elgg_type in ['longtext']:
            field_type = 'html_field'
        elif elgg_type in ['multiselect']:
            field_type = 'multi_select_field'
        else:
            field_type = 'text_field'

        return field_type

    def get_profile_category(self, name):
        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return None

        category_guid = profile_field_entity.get_metadata_value_by_name('category_guid')

        if category_guid:
            category_entity = ElggEntities.objects.using(self.database).filter(
                subtype__subtype="custom_profile_field_category",
                guid=category_guid
            ).first()

            if category_entity:
                if category_entity.get_metadata_value_by_name('metadata_label'):
                    return category_entity.get_metadata_value_by_name('metadata_label')
                if category_entity.get_metadata_value_by_name('metadata_name'):
                    return category_entity.get_metadata_value_by_name('metadata_name')

        return None

    def get_profile_options(self, name):
        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return []

        metadata_type = profile_field_entity.metadata.filter(name__string="metadata_options").first()

        options = metadata_type.value.string.split(',') if metadata_type else []
        return options

    def get_profile_is_editable(self, name):
        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return True

        metadata_type = profile_field_entity.metadata.filter(name__string="user_editable").first()

        editable = metadata_type.value.string == 'yes' if metadata_type else True # default True
        return editable

    def get_profile_is_mandatory(self, name):
        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return False

        metadata_type = profile_field_entity.metadata.filter(name__string="mandatory").first()

        return metadata_type.value.string == 'yes' if metadata_type else False # default False

    def get_profile_is_in_onboarding(self, name):
        profile_field_entity= self.get_profile_field(name)

        if not profile_field_entity:
            return False

        metadata_type = profile_field_entity.metadata.filter(name__string="show_on_register").first()

        return metadata_type.value.string == 'yes' if metadata_type else False # default False

    def get_menu(self, menu_input):

        menu = []

        for item in menu_input:
            if 'children' not in item:
                item["children"] = []
            menu.append(item)

        return menu

    def get_profile_sections(self, profile):
        sections = [""]
        profile_sections = []
        for item in profile:
            category = self.get_profile_category(item['key'])
            if category and category not in sections:
                sections.append(category)
        for section in sections:
            profile_field_guids = []
            for item in profile:
                category = self.get_profile_category(item['key'])
                if not category:
                    category = ""
                if category == section:
                    profile_field_guids.append(str(ProfileField.objects.get(key=item['key']).id))
            profile_sections.append({"name": section, "profileFieldGuids": profile_field_guids})

        return profile_sections

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

    def save_parent_wiki(self, elgg_wiki):
        guid_map_wiki = GuidMap.objects.get(id=elgg_wiki.entity.guid, object_type='wiki')
        wiki = Wiki.objects.get(id=guid_map_wiki.guid)

        try:
            guid_map_parent = GuidMap.objects.get(id=elgg_wiki.entity.container_guid, object_type='wiki')
            parent = Wiki.objects.get(id=guid_map_parent.guid)
            wiki.parent = parent
            wiki.save()

        except Exception:
            pass

    def update_wiki_children_acl(self, wiki):
        for child in wiki.children.all():
            # set Group
            if child.group != wiki.group:
                child.group = wiki.group

            # check elgg ACL if exists
            in_guid_map = GuidMap.objects.filter(guid=child.guid).first()
            if in_guid_map:
                elgg_entity = ElggObjectsEntity.objects.using(self.database).filter(entity__guid=in_guid_map.id).first()
                if elgg_entity:
                    write_access_id = int(elgg_entity.entity.get_metadata_value_by_name("write_access_id")) \
                        if elgg_entity.entity.get_metadata_value_by_name("write_access_id") else 0

                    child.write_access = self.elgg_access_id_to_acl(child, write_access_id)
                    child.read_access = self.elgg_access_id_to_acl(child, elgg_entity.entity.access_id)
                    child.save()

            child.save()

            # recursive
            self.update_wiki_children_acl(child)

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
        if not filename:
            return None

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

        if not elgg_entity.entity.get_metadata_value_by_name("featuredIcontime") \
            or int(elgg_entity.entity.get_metadata_value_by_name("featuredIcontime")) == 0:
            return None

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
            entity.title = filename
            entity.upload.name = file_path

            entity.owner = self.get_user_or_admin(elgg_entity.entity.owner_guid)

            entity.is_folder = False

            entity.read_access = self.elgg_access_id_to_acl(entity, 2)
            entity.write_access = self.elgg_access_id_to_acl(entity, 0)

            entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
            entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

            entity.save()
            return entity
        except Exception:
            return None

    def save_and_get_group_icon(self, elgg_entity):

        if not elgg_entity.entity.get_metadata_value_by_name("icontime") \
            or int(elgg_entity.entity.get_metadata_value_by_name("icontime")) == 0:
            return None

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
            entity.title = filename
            entity.upload.name = file_path

            entity.owner = group_owner

            entity.is_folder = False

            entity.read_access = self.elgg_access_id_to_acl(entity, 2)
            entity.write_access = self.elgg_access_id_to_acl(entity, 0)

            entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
            entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

            entity.save()

            return entity

        except Exception:
            return None

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
                "migrated", year, month, day, str(elgg_site.entity.guid), 'pleio_template', filename
            )

            if default_storage.exists(file_path):
                entity = FileFolder()

                entity.owner = User.objects.filter(roles__contains=['ADMIN']).first()

                entity.upload.name = file_path
                entity.mime_type = mime_type
                entity.title = filename

                entity.read_access = self.elgg_access_id_to_acl(entity, 2)
                entity.write_access = self.elgg_access_id_to_acl(entity, 0)

                entity.save()

                return entity.embed_url
            return ""
        except Exception:
            return ""

    def save_entity_annotations(self, elgg_entity, entity, annotation_types=['vote', 'bookmark', 'follow', 'view_count', 'views']):
        # pylint: disable=dangerous-default-value
        # pylint: disable=too-many-locals
        if "vote" in annotation_types:
            annotations = elgg_entity.entity.annotation.filter(name__string="vote", value__string="1")
            for vote in annotations:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=vote.owner_guid, object_type="user").guid)
                    entity.add_vote(user, 1)
                except Exception:
                    print("Annotation vote, user not found")
        if "bookmark" in annotation_types:
            bookmarks = elgg_entity.entity.relation_inverse.filter(relationship="bookmarked", right__guid=elgg_entity.entity.guid)
            for bookmark in bookmarks:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=bookmark.left.guid, object_type="user").guid)
                    entity.add_bookmark(user)
                except Exception:
                    print("Annotation bookmark, user not found")
        if "follow" in annotation_types:
            follows = elgg_entity.entity.relation_inverse.filter(relationship="content_subscription", right__guid=elgg_entity.entity.guid)
            for follow in follows:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=follow.left.guid, object_type="user").guid)
                    entity.add_follow(user)
                except Exception:
                    print("Annotation follow, user not found")

        if "view_count" in annotation_types:
            view_count = ElggEntityViews.objects.using(self.database).filter(guid=elgg_entity.entity.guid).first()
            if view_count:
                EntityViewCount.objects.create(entity=entity, views=view_count.views)
        if "views" in annotation_types:
            try:
                user_ids = list(ElggEntityViewsLog.objects.using(self.database).filter(
                    entity_guid=elgg_entity.entity.guid).values_list('performed_by_guid', flat=True)
                )
                user_guids = list(GuidMap.objects.filter(id__in=user_ids, object_type="user").values_list('guid', flat=True))
                users = User.objects.filter(id__in=user_guids)
                if users:
                    for user in users:
                        EntityView.objects.create(entity=entity, viewer=user)
            except Exception:
                print("Annotation views, not saved")

    def elgg_access_id_to_acl(self, obj, access_id):
        """
        Overwritten from core.lib because elgg uses access_id >= 3 for groups and we have to detect subgroups
        """
        access_id = int(access_id)
        if access_id >= 3:

            # test if object has attr group and group is not None
            if hasattr(obj, 'group') and obj.group:
                access_collection = ElggAccessCollections.objects.using(self.database).filter(id=access_id).first()
                if access_collection and not access_collection.name[:6] in ['Groep:', 'Group:']:
                    subgroup = obj.group.subgroups.filter(name=access_collection.name).first()
                    if subgroup:
                        # subgroup found use Subgroup.access_id
                        access_id = subgroup.access_id
                    else:
                        # subgroup does not exist anymore?
                        access_id = 0
                elif access_collection:
                    # access_collection is group
                    access_id = 4
                else:
                    # access_collection does not exist?
                    access_id = 0
            else:
                # if not in group there are also no subgroups
                access_id = 0

        return access_id_to_acl(obj, access_id)

    def get_user_or_admin(self, entity_guid):
        """
        Try to get owner, if it doesnt exist return first admin user.
        """
        try:
            owner = User.objects.get(id=GuidMap.objects.get(id=entity_guid, object_type='user').guid)
        except Exception:
            owner = User.objects.filter(roles__contains=['ADMIN']).first()

        return owner

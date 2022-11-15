import json
from collections import defaultdict
from typing import Union

from core import config
from core.models import UserProfile, Entity, Group, Widget, Tag
from core.models.tags import EntityTag


class MigrationBase:
    category_table = {}

    def __init__(self):
        for collection in config.TAG_CATEGORIES:
            for value in collection['values']:
                self.category_table[value.lower()] = {
                    "name": collection['name'],
                    "value": value,
                }

    def run(self):
        if self.category_table:
            self._run()

    def _run(self):
        raise NotImplementedError()


class UserMigration(MigrationBase):

    def _run(self):
        try:
            assert self.category_table
            for profile in UserProfile.objects.filter(overview_email_tags__isnull=False):
                self.migrate_user(profile)
        except Exception:
            pass

    def migrate_user(self, profile):
        if profile.overview_email_categories:
            return

        try:
            category_tags = defaultdict(lambda: {'values': []})
            new_tags = []
            for tag in profile.overview_email_tags:
                if tag.lower() in self.category_table:
                    spec = self.category_table[tag.lower()]
                    category_tags[spec['name']]['name'] = spec['name']
                    category_tags[spec['name']]['values'].append(spec['value'])
                else:
                    new_tags.append(tag)
            profile.overview_email_tags = new_tags
            profile.overview_email_categories = [category for category in category_tags.values()]
            profile.save()
        except Exception:
            pass


class EntityMigration(MigrationBase):

    def _run(self):
        for entity in Entity.objects.filter(_tag_summary__isnull=False).select_subclasses():
            self.migrate_entity(entity)

    def migrate_entity(self, entity: Union[(Entity, Group)]):
        if entity.category_tags:
            return

        try:
            category_tags = defaultdict(lambda: {'values': []})
            current_tags = EntityTag.objects.filter(entity_id=entity.pk)
            new_tags = []
            for tag in current_tags:
                if tag.tag.label in self.category_table:
                    spec = self.category_table[tag.tag.label]
                    category_tags[spec['name']]['name'] = spec['name']
                    category_tags[spec['name']]['values'].append(spec['value'])
                else:
                    new_tags.append(tag.author_label)
            entity.tags = new_tags
            entity.category_tags = [category for category in category_tags.values()]
            entity.save()
        except Exception:
            pass


class GroupMigration(EntityMigration):

    def _run(self):
        for group in Group.objects.filter(_tag_summary__isnull=False):
            self.migrate_entity(group)


class WidgetMigration(MigrationBase):

    def _run(self):
        for widget in Widget.objects.all():
            self.migrate_widget(widget)

    def migrate_widget(self, widget: Widget):
        try:
            changed = False
            new_settings = []
            for setting in widget.settings:
                if setting['key'] == 'categoryTags':
                    try:
                        json.loads(setting['value'])
                    except json.decoder.JSONDecodeError:
                        # if not json:
                        setting['value'] = self.translate_widget_tags(setting['value'])
                        changed = True
                if setting['key'] == 'tagFilter':
                    setting['value'] = self.translate_widget_tagfilter(setting['value'])
                    changed = True
                new_settings.append(setting)

            if changed:
                widget.settings = new_settings
                widget.save()
        except Exception:
            pass

    def translate_widget_tags(self, value: str):
        category_tags = defaultdict(lambda: {'values': []})
        for tag in value.split(','):
            tag = tag.strip().lower()
            if tag in self.category_table:
                spec = self.category_table[tag]
                category_tags[spec['name']]['name'] = spec['name']
                category_tags[spec['name']]['values'].append(spec['value'])
        return json.dumps([c for c in category_tags.values()])

    def translate_widget_tagfilter(self, value):
        try:
            setting = json.loads(value)
            if not isinstance(setting, dict):
                return value

            category_tags = defaultdict(lambda: {'values': []})
            for values in setting.values():
                for tag in values:
                    tag = tag.lower()
                    if tag not in self.category_table:
                        continue
                    spec = self.category_table[tag]
                    category_tags[spec['name']]['name'] = spec['name']
                    category_tags[spec['name']]['values'].append(spec['value'])
            return json.dumps([c for c in category_tags.values()])
        except Exception:
            pass
        return value


def cleanup():
    Tag.objects.exclude(pk__in={t.tag.id for t in EntityTag.objects.all()}).delete()

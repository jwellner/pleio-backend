import json
from collections import defaultdict

from core.models import Entity, Group, Widget


class TagCategoryCollector:
    repository = defaultdict(set)

    def add(self, name, value):
        self.repository[name].add(value)

    def get_tag_categories(self):
        tag_categories = []
        for name in sorted(self.repository.keys()):
            tag_categories.append({
                'name': name,
                'values': [v for v in sorted(self.repository[name])]
            })
        return tag_categories

    def loop_entities(self, qs):
        for category_tags in qs.values_list('category_tags', flat=True):
            if category_tags:
                for category_tag in category_tags:
                    for value in category_tag['values']:
                        self.add(category_tag['name'], value)

    def loop_widget_settings(self, qs):
        for widget in qs:
            for setting in widget.settings:
                if setting['key'] in ['categoryTags', 'tagFilter']:
                    try:
                        for category_tag in json.loads(setting['value']):
                            for value in category_tag['values']:
                                self.add(category_tag['name'], value)
                    except Exception:
                        pass


def reconstruct_tag_categories():
    tag_collector = TagCategoryCollector()
    tag_collector.loop_entities(Entity.objects.all().select_subclasses())
    tag_collector.loop_entities(Group.objects.all())
    tag_collector.loop_widget_settings(Widget.objects.all())

    return tag_collector.get_tag_categories()

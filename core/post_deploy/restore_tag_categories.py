import json
import os.path
from collections import defaultdict

from core import config
from core.lib import is_schema_public, tenant_schema

from post_deploy import post_deploy_action

from core.models import Entity, Group, Widget, TagsModel, UserProfile


@post_deploy_action(auto=False)
def restore_tag_categories():
    if is_schema_public():
        return

    # Step one: restore the TAG_CATEGORIES value if needed.
    json_filename = os.path.join(os.path.dirname(__file__), 'assets', 'all_tag_categories-22-11-02.json')
    with open(json_filename, 'r') as fh:
        data = json.load(fh) or {}

    old_tag_categories = data.get(tenant_schema()) or []
    if old_tag_categories and not config.TAG_CATEGORIES:
        config.TAG_CATEGORIES = old_tag_categories

    # Step two: re-process content, given the new tag_categories.
    restore_content_tag_categories(config.TAG_CATEGORIES)


def restore_content_tag_categories(old_tag_categories):
    restorer = CategoryRestorer(old_tag_categories)
    for entity in Entity.objects.all().select_subclasses():
        restorer.process_article(entity)
    for group in Group.objects.all():
        restorer.process_article(group)
    for widget in Widget.objects.all():
        restorer.process_widget(widget)
    for profile in UserProfile.objects.all():
        restorer.process_profile(profile)


class CategoryRestorer:
    def __init__(self, tag_categories):
        self.categories = []
        self.category_repository = {}
        self.tag_repository = {}
        for tag_category in tag_categories:
            self.categories.append(tag_category['name'])
            self.category_repository[tag_category['name']] = tag_category['values']
            for value in tag_category['values']:
                self.tag_repository[value] = tag_category['name']

    def process_article(self, article: TagsModel):
        original_tags = article.tags
        original_categories = article.category_tags

        all_tags = article.tags
        for category_tag in article.category_tags:
            for value in category_tag['values']:
                all_tags.append(value)

        new_tags = []
        new_category_tags = defaultdict(list)

        for tag in all_tags:
            if tag in self.tag_repository:
                new_category_tags[self.tag_repository[tag]].append(tag)
            else:
                new_tags.append(tag)
        article.tags = new_tags
        article.category_tags = [{'name': name, "values": values} for name, values in new_category_tags.items()]

        if article.tags != original_tags or article.category_tags != original_categories:
            article.save()

    def process_widget(self, widget: Widget):
        new_settings = []
        changed = False
        for setting in widget.settings:
            if setting['key'] in ['tagFilter', 'categoryTags']:
                try:
                    original_tags = setting['value']
                    new_category_tags = defaultdict(list)
                    category_tags = json.loads(setting['value'])
                    for category_tag in category_tags:
                        for tag in category_tag['values']:
                            if tag not in self.tag_repository:
                                continue
                            new_category_tags[self.tag_repository[tag]].append(tag)
                    setting['value'] = json.dumps([{"name": name, "values": values} for name, values in new_category_tags.items()])
                    if setting['value'] != original_tags:
                        changed = True
                except Exception:
                    pass
            new_settings.append(setting)

        if changed:
            widget.settings = new_settings
            widget.save()

    def process_profile(self, profile: UserProfile):
        original_tags = profile.overview_email_tags
        original_categories = profile.overview_email_categories

        all_tags = profile.overview_email_tags
        for category_tag in profile.overview_email_categories:
            for value in category_tag['values']:
                all_tags.append(value)

        new_tags = []
        new_category_tags = defaultdict(list)

        for tag in all_tags:
            if tag in self.tag_repository:
                new_category_tags[self.tag_repository[tag]].append(tag)
            else:
                new_tags.append(tag)
        profile.overview_email_tags = new_tags
        profile.overview_email_categories = [{'name': name, "values": values} for name, values in new_category_tags.items()]

        if profile.overview_email_tags != original_tags or profile.overview_email_categories != original_categories:
            profile.save()

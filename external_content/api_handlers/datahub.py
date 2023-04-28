import json
import logging
from collections import defaultdict

import requests
import urllib.parse

from django.core.exceptions import ValidationError
from django.utils import timezone

from core import config
from external_content.api_handlers import ApiHandlerBase, ApiHandlerError
from external_content.models import ExternalContent

logger = logging.getLogger(__name__)


class DataHubClient:

    def __init__(self, base_url, batch_size=None):
        self.base_url = base_url
        self.batch_size = batch_size or 50

    def get(self, resource, since: timezone.datetime = None):
        response = requests.get(urllib.parse.urljoin(self.base_url, resource), {
            "limit": self.batch_size,
            "format": "json",
            **({"modified_after": since.isoformat()} if since else {}),
        }, timeout=300)
        if not response.ok:
            raise ApiHandlerError("%s: %s" % (response.status_code, response.reason))
        yield from self.iterate_results(response.json())

    def iterate_results(self, data):
        for record in data.get('results') or []:
            yield record

        if data.get('next'):
            response = requests.get(data['next'], timeout=300)
            if not response.ok:
                raise ApiHandlerError("%s: %s" % (response.status_code, response.reason))
            yield from self.iterate_results(response.json())


class TagCollector:
    def __init__(self, *values):
        self.values = set(values)

    def add_value(self, *values):
        self.values.update(values)
        return self

    def get_values(self):
        return list(self.values)

    def as_dict(self, name):
        if self.values:
            return {
                'name': name,
                'values': sorted(list(self.values), key=lambda x: str(x).lower())
            }

    def __str__(self):
        return "<TagCollector %s>" % str(self.values)

    def __cmp__(self, other):
        return self.values == other.values


class ApiHandler(ApiHandlerBase):
    ID = 'datahub'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.study_zones = {}
        self.tag_categories = defaultdict(TagCollector)
        self.client = DataHubClient(self.source.settings['apiUrl'],
                                    self.source.settings['batchSize'])
        self.imported_files = []

    def should_do_full_sync(self):
        return not self.source.last_full_sync or self.source.last_full_sync < timezone.now() - timezone.timedelta(days=1)

    def should_do_update(self):
        return self.source.last_update_sync and self.source.last_update_sync < timezone.now() - timezone.timedelta(hours=1)

    def pull(self):
        if not config.DATAHUB_EXTERNAL_CONTENT_ENABLED:
            return

        if self.should_do_full_sync():
            self.full_sync()
        elif self.should_do_update():
            self.update(self.source.last_update_sync - timezone.timedelta(hours=1))

    def full_sync(self):
        self.pull_study_zones()
        self.pull_files()
        self.apply_tags()
        self.cleanup_files()

        self.source.set_full_sync(timezone.now())
        self.source.set_update_sync(timezone.now())

    def update(self, since):
        self.pull_study_zones()
        self.pull_files(since)

        self.source.set_update_sync(timezone.now())

    def pull_study_zones(self):
        self.study_zones = {}
        for study in self.client.get('studies'):
            self.study_zones[study['name']] = []
            for zone in study.get('zones') or []:
                self.study_zones[study['name']].append(zone['name'])

    def pull_files(self, since=None):
        for record in self.client.get('files', since):
            self.import_file(record)

    def import_file(self, record):
        try:
            tag_categories = filter(bool, [
                self._load_tags('classification', record).as_dict("classification"),
                self._load_tags('sensor', record).as_dict("sensor"),
                self._load_tags('study', record).as_dict("study"),
                self._load_tags('extension', record).as_dict("extension"),
                self._load_tags('chapter', record).as_dict("chapter"),
                self._load_zone(record).as_dict("zone"),
            ])

            remote_id = "%s:%s" % (self.source.guid, record['id'])
            file = ExternalContent.objects.filter(remote_id=remote_id).first()
            if not file:
                file = ExternalContent()
                file.source = self.source
                file.owner = self.owner
                file.remote_id = remote_id
                file.created_at = record['date_created']

            file.title = record['name'] or ''
            file.updated_at = record['date_modified']
            file.description = record['description'] or ''
            file.category_tags = [t for t in tag_categories]
            file.canonical_url = self._get_canonical_url(record)
            file.save()
            self.imported_files.append(file.guid)
        except ValidationError as e:
            raise Exception("Record: %s" % json.dumps(record))

    def _load_tags(self, category, record):
        try:
            tags = TagCollector(record[category]['name'])
            self.tag_categories[category].add_value(*tags.get_values())
            return tags
        except (AttributeError, KeyError, TypeError):
            return TagCollector()

    def _load_zone(self, record):
        try:
            study = record['study']['name']
            zone_tags = TagCollector(*self.study_zones[study])
            self.tag_categories['zone'].add_value(*zone_tags.get_values())
            return zone_tags
        except (AttributeError, KeyError):
            return TagCollector()

    def _get_canonical_url(self, record):
        pk = str(record['id'])
        prefix = self.source.settings['frontendUrl']
        return urllib.parse.urljoin(prefix, pk)

    def apply_tags(self):
        new_categories = {c['name']: c for c in config.TAG_CATEGORIES}
        for name, tags in self.tag_categories.items():
            category = tags.as_dict(name)
            if name in new_categories:
                new_categories[name]['values'] = category['values']
            else:
                new_categories[name] = category

        config.TAG_CATEGORIES = [c for c in new_categories.values()]

    def cleanup_files(self):
        ExternalContent.objects.exclude(id__in=self.imported_files).delete()

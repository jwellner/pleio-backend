import uuid

from django.db import models
from django.utils import timezone

from core.lib import str_to_datetime
from core.models import Entity
from core.utils.entity import load_entity_by_id


class Revision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey('user.User', on_delete=models.CASCADE, null=True)

    _container = models.ForeignKey(Entity, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        self.original = {}
        super().__init__(*args, **kwargs)

    @property
    def container(self):
        return load_entity_by_id(self._container.id, [Entity])

    def update_container(self, container):
        Revision.objects.filter(id=self.guid).update(_container=container)

    description = models.TextField(null=True, blank=True)
    content = models.JSONField(default=dict)
    previous_content = models.JSONField(default=dict)
    unchanged = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    is_update = models.BooleanField(default=False)
    attachments = models.JSONField(default=list)

    def lookup_attachments(self):
        return self.attachments

    def _load_attachments(self, container):
        if not hasattr(container, 'lookup_attachments'):
            self.attachments = []
        else:
            self.attachments = [str(id) for id in container.lookup_attachments()]

    def _filter_unique_attachments(self, container):
        if not hasattr(container, 'lookup_attachments'):
            return
        combined_attachments = {*self.attachments, *[str(id) for id in container.lookup_attachments()]}
        self.attachments = [*combined_attachments]

    def start_tracking_changes(self, container):
        self._load_attachments(container)
        self.original = container.serialize()

    def store_initial_version(self, container):
        self._container = container
        self.author = container.owner
        self.content = container.serialize()
        self._load_attachments(container)
        self.save()

    def store_update_revision(self, container):
        self._container = container
        self.content = {}
        for key, value in container.serialize().items():
            if self.original[key] == value:
                self.unchanged[key] = value
            else:
                self.content[key] = value
                self.previous_content[key] = self.original[key]
        self.is_update = True
        self._filter_unique_attachments(container)
        self.save()

    def store_publication_revision(self, container, previous_status):
        self.original['statusPublished'] = previous_status
        self.store_update_revision(container)

    def serialize_previous_version(self):
        return {
            **self.unchanged,
            **self.previous_content,
        }

    @property
    def guid(self):
        return str(self.id)

    class Meta:
        ordering = ('-created_at',)


def _is_timestamp_equal(left, right):
    return str_to_datetime(left) == str_to_datetime(right)


def _is_listing_equal(left, right, exact=True):
    if exact:
        return (left or []) == (right or [])
    return set(left) == set(right)


def _is_boolean_equal(left, right):
    return bool(left) == bool(right)

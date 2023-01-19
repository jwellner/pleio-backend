import uuid
from traceback import format_exc

from django.db import models
from django.utils import timezone

from core import config
from core.constances import ACCESS_TYPE
from core.models.entity import Entity


class ExternalContent(Entity):
    source = models.ForeignKey('external_content.ExternalContentSource', on_delete=models.CASCADE)

    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    remote_id = models.CharField(max_length=256)
    canonical_url = models.URLField()

    def can_write(self, user):
        return False

    @property
    def guid(self):
        return str(self.id)

    @property
    def url(self):
        return self.canonical_url

    @property
    def type_to_string(self):
        return self.source.guid

    def serialize(self):
        return {}

    def save(self, *args, **kwargs):
        if self._state.adding:
            self._sync_access_arrays()
        self.full_clean()
        super().save(*args, **kwargs)

    def _sync_access_arrays(self):
        self.read_access = [ACCESS_TYPE.logged_in] if config.IS_CLOSED else [ACCESS_TYPE.public]
        self.write_access = [ACCESS_TYPE.user.format(self.owner.guid)]

    def __str__(self):
        return "<ExternalContent[%s] %s>" % (self.source.name, self.title)

    def __repr__(self):
        try:
            return self.__str__()
        except Exception as e:
            return "Assertion error at __repr__"


class ExternalContentSource(models.Model):
    class Meta:
        ordering = ('handler_id', 'name',)

    handlers = {}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=256)
    plural_name = models.CharField(max_length=256)
    handler_id = models.CharField(max_length=128)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    last_full_sync = models.DateTimeField(default=None, null=True)
    last_update_sync = models.DateTimeField(default=None, null=True)

    @property
    def guid(self):
        return str(self.id)

    def get_handler(self):
        assert self.handler_id in self.get_handlers()
        return self.get_handlers()[self.handler_id](self)

    def set_full_sync(self, value):
        ExternalContentSource.objects.filter(id=self.id).update(last_full_sync=value)

    def set_update_sync(self, value):
        ExternalContentSource.objects.filter(id=self.id).update(last_update_sync=value)

    @classmethod
    def get_handlers(cls):
        from external_content.utils import find_handlers
        if not cls.handlers:
            cls.handlers = {id: c for id, c in find_handlers()}
        return cls.handlers

    def pull(self):
        from external_content.api_handlers import ApiHandlerBase
        try:
            handler: ApiHandlerBase = self.get_handler()
            handler.pull()
            ExternalContentFetchLog.objects.create(
                source=self,
                success=True
            )
        except Exception as e:
            ExternalContentFetchLog.objects.create(
                source=self,
                success=False,
                message=format_exc()
            )


class ExternalContentFetchLog(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    source = models.ForeignKey('external_content.ExternalContentSource', on_delete=models.CASCADE)
    success = models.BooleanField()
    message = models.TextField()

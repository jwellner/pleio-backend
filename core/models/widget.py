import uuid
from auditlog.registry import auditlog
from django.db import models
from django.contrib.postgres.fields import ArrayField

from core.models.rich_fields import AttachmentMixin, Attachment


class Widget(AttachmentMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        'core.Group',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    settings = ArrayField(models.JSONField(help_text="Please provide valid JSON data"), blank=True, default=list)
    position = models.IntegerField(null=False)
    type = models.CharField(max_length=64)
    page = models.ForeignKey(
        'cms.Page',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    column = models.ForeignKey(
        'cms.Column',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )

    @property
    def guid(self):
        return str(self.id)

    def can_write(self, user):
        if self.group:
            return self.group.can_write(user)

        if self.page:
            return self.page.can_write(user)

        return False

    def can_read(self, user):
        if self.page:
            return self.page.can_read(user)

        return False

    @property
    def type_to_string(self):
        return 'widget'

    def __str__(self):
        return f"Widget[{self.guid}]"

    @property
    def rich_fields(self):

        def get_value(setting):
            return setting.get('richDescription', '') or setting.get('value', '')

        def is_rich_field(setting):
            if setting.get('key', '') == 'richDescription':
                return True
            return False

        return [get_value(setting) for setting in self.settings if is_rich_field(setting)]

    def attachments_in_fields(self):
        """
        Override AttachmentMixin method
        """
        attachment_ids = [setting.get('attachment') for setting in self.settings if setting.get('attachment', None)]

        return Attachment.objects.filter(id__in=attachment_ids)

    def get_setting_value(self, key):
        for setting in self.settings:
            if setting['key'] == key:
                return setting['value']


auditlog.register(Widget)

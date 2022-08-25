import uuid

from django.db import models
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _


class AvatarExport(models.Model):
    class Meta:
        ordering = ('-created_at',)

    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("in_progress", _("In progress")),
        ("ready", _("Ready")),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    initiator = models.ForeignKey('user.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=localtime)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.ForeignKey('file.FileFolder', on_delete=models.CASCADE, null=True)

    @property
    def guid(self):
        return str(self.id)

    @property
    def is_ready(self):
        return self.status == 'ready'

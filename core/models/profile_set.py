import uuid

from django.db import models


class ProfileSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    field = models.ForeignKey('core.ProfileField', on_delete=models.CASCADE)
    users = models.ManyToManyField('user.User', related_name="profile_sets")

    @property
    def guid(self):
        return str(self.pk)
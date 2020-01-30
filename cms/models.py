import uuid
from django.db import models
from core.models import Entity
from django.contrib.postgres.fields import ArrayField


class Page(Entity):
    """
    Page for CMS
    """
    PAGE_TYPES = (
        ('campagne', 'Campagne'),
        ('text', 'Text')
    )

    class Meta:
        ordering = ['position', '-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    page_type = models.CharField(max_length=256, choices=PAGE_TYPES)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    position = models.IntegerField(null=False, default=0)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def can_write(self, user):
        if user.is_authenticated and user.is_admin:
            return True
        return False

    def __str__(self):
        return self.title

    def type_to_string(self):
        return 'page'


class Row(models.Model):
    """
    Row for CMS
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    position = models.IntegerField(null=False)
    is_full_width = models.BooleanField(default=False)
    parent_id = models.UUIDField(default=uuid.uuid4)
    page = models.ForeignKey('Page', related_name='rows', on_delete=models.CASCADE)

    @property
    def guid(self):
        return str(self.id)

    def type_to_string(self):
        return 'row'

class Column(models.Model):
    """
    Column for CMS
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    position = models.IntegerField(null=False)
    width = ArrayField(models.IntegerField())
    parent_id = models.UUIDField(default=uuid.uuid4)
    page = models.ForeignKey('Page', related_name='columns', on_delete=models.CASCADE)

    @property
    def guid(self):
        return str(self.id)

    def type_to_string(self):
        return 'column'

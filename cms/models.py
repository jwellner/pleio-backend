import uuid
from auditlog.registry import auditlog
from django.db import models
from core.models import Entity
from core.constances import USER_ROLES
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify


class Page(Entity):
    """
    Page for CMS
    """
    PAGE_TYPES = (
        ('campagne', 'Campagne'),
        ('text', 'Text')
    )

    class Meta:
        # When positions are equal sort old -> new (used for menu's)
        ordering = ['position', 'created_at']

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
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True
        return False

    def __str__(self):
        return f"Page[{self.title}]"

    @property
    def url(self):
        return '/cms/view/{}/{}'.format(
            self.guid, slugify(self.title)
        ).lower()

    @property
    def type_to_string(self):
        return 'page'


class Row(models.Model):
    """
    Row for CMS
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    position = models.IntegerField(null=False)
    is_full_width = models.BooleanField(default=False)

    page = models.ForeignKey('Page', related_name='rows', on_delete=models.CASCADE)

    @property
    def guid(self):
        return str(self.id)

    @property
    def type_to_string(self):
        return 'row'

    def __str__(self):
        return f"Row[{self.guid}]"

class Column(models.Model):
    """
    Column for CMS
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    position = models.IntegerField(null=False)
    width = ArrayField(models.IntegerField())
    row = models.ForeignKey(
        'cms.Row',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='columns'
    )
    page = models.ForeignKey('Page', related_name='columns', on_delete=models.CASCADE)

    @property
    def guid(self):
        return str(self.id)

    @property
    def type_to_string(self):
        return 'column'

    def __str__(self):
        return f"Column[{self.guid}]"


auditlog.register(Page)
auditlog.register(Row)
auditlog.register(Column)
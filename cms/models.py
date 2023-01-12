import uuid
from auditlog.registry import auditlog
from django.db import models

from cms.row_resolver import RowSerializer
from core.lib import get_access_id
from core.models import Entity, AttachmentMixin, RevisionMixin
from core.constances import USER_ROLES
from django.contrib.postgres.fields import ArrayField

from core.models.mixin import TitleMixin, RichDescriptionMediaMixin

from core.models.rich_fields import ReplaceAttachments


class Page(RichDescriptionMediaMixin, TitleMixin, AttachmentMixin, RevisionMixin, Entity):
    """
    Page for CMS
    """
    PAGE_TYPES = (
        ('campagne', 'Campagne'),
        ('text', 'Text')
    )

    class Meta:
        # When positions are equal sort old -> new (used for menu's)
        ordering = ['position', 'published']

    rich_description = models.TextField(null=True, blank=True)

    page_type = models.CharField(max_length=256, choices=PAGE_TYPES)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    row_repository = models.JSONField(null=True, default=list)

    position = models.IntegerField(null=False, default=0)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def can_write(self, user):
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True
        return False

    def has_revisions(self):
        return self.page_type == 'text'

    def __str__(self):
        return f"Page[{self.title}]"

    @property
    def url(self):
        return '/cms/view/{}/{}'.format(
            self.guid, self.slug
        ).lower()

    @property
    def type_to_string(self):
        return 'page'

    @property
    def parents(self):
        parents = []
        child = self
        while child.parent:
            if child.parent in parents:
                break
            parents.append(child.parent)
            child = child.parent
        return [page for page in reversed(parents)]

    @property
    def rich_fields(self):
        return [field for field in self.attachments_from_rich_fields()]

    def attachments_from_rich_fields(self):
        if self.rich_description:
            yield self.rich_description
        for row in self.row_repository or []:
            yield from RowSerializer(row).rich_fields()

    def lookup_attachments(self):
        yield from super().lookup_attachments()
        yield from self.attachments_in_rows()

    def attachments_in_rows(self):
        for row in [RowSerializer(r) for r in self.row_repository]:
            yield from row.attachments()

    def replace_attachments(self, attachment_map: ReplaceAttachments):
        super().replace_attachments(attachment_map)
        for row_id, row in self.row_repository:
            for column_id, column in row['columns']:
                for widget_id, widget in enumerate(column['widgets']):
                    for setting_id, setting in enumerate(widget.settings):
                        current_id = setting.get('attachmentId')
                        if attachment_map.has_attachment(current_id):
                            setting['attachmentId'] = attachment_map.translate(current_id)
                        if setting['key'] == 'richDescription' or setting.get('richDescription'):
                            setting['richDescription'] = attachment_map.replace(setting['richDescription'] or setting['value'])
                            setting['value'] = None
                        self.row_repository[row_id]['columns'][column_id]['widgets'][widget_id]['settings'][setting_id] = setting

    def serialize(self):
        if self.has_revisions():
            return {
                'title': self.title or '',
                'richDescription': self.rich_description or '',
                'tags': sorted(self.tags) or [],
                'tagCategories': self.category_tags or [],
                'accessId': get_access_id(self.read_access),
                'statusPublished': self.status_published,
            }
        return {}

    def get_media_status(self):
        if self.page_type == 'campagne':
            return False
        return super().get_media_status()


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

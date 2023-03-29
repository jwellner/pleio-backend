import uuid
from copy import deepcopy

from auditlog.registry import auditlog
from django.db import models

from cms.row_resolver import RowSerializer
from core.models import Entity, AttachmentMixin, RevisionMixin
from core.constances import USER_ROLES
from django.contrib.postgres.fields import ArrayField

from core.models.mixin import TitleMixin, RichDescriptionMediaMixin

from core.models.rich_fields import ReplaceAttachments
from core.widget_resolver import WidgetSerializer


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

    def update_widgets(self, callback):
        new_rows = []
        for row in self.row_repository:
            new_columns = []
            for column in row['columns']:
                column['widgets'] = [callback(w) for w in column.get('widgets') or []]
                new_columns.append(column)
            row['columns'] = new_columns
            new_rows.append(row)
        self.row_repository = new_rows

    def replace_attachments(self, attachment_map: ReplaceAttachments):
        super().replace_attachments(attachment_map)

        def update_attachments(widget):
            new_settings = []
            for setting in widget.get('settings', []):
                current_id = setting.get('attachmentId')
                if attachment_map.has_attachment(current_id):
                    setting['attachmentId'] = attachment_map.translate(current_id)
                if setting['key'] == 'richDescription' or setting.get('richDescription'):
                    setting['richDescription'] = attachment_map.replace(setting['richDescription'] or setting['value'])
                    setting['value'] = None
                new_settings.append(setting)
            widget['settings'] = new_settings
            return widget

        self.update_widgets(update_attachments)

    def map_rich_text_fields(self, callback):
        self.rich_description = callback(self.rich_description)

        def change_rich_widget(widget):
            widget_serializer = WidgetSerializer(widget)
            widget_serializer.map_rich_fields(callback)
            return widget_serializer.serialize()

        if self.row_repository:
            self.update_widgets(change_rich_widget)

    def serialize(self):
        return {
            'title': self.title or '',
            'richDescription': self.rich_description or '',
            'parentGuid': self.parent.guid if self.parent else '',
            'position': self.position,
            'rows': deepcopy(self.row_repository),
            **super().serialize(),
        }

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

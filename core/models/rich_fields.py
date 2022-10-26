import abc
from core.models.attachment import Attachment
from core.models.shared import AbstractModel
from core.utils.tiptap_parser import Tiptap
from core.lib import is_valid_uuid
from django.contrib.contenttypes.fields import GenericRelation
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from .mixin import NotificationMixin


class RichFieldsMixin(AbstractModel):
    class Meta:
        abstract = True

    @property
    @abc.abstractmethod
    def rich_fields(self):
        """ Return a list of Tiptap objects e.g. [self.rich_description]. These are parsed and used to find mentioned users """


class MentionMixin(NotificationMixin, RichFieldsMixin):
    class Meta:
        abstract = True

    @property
    def mentioned_users(self):
        user_ids = set()
        for tiptap in self.rich_fields:
            parser = Tiptap(tiptap)
            user_ids.update(parser.mentioned_users)

        return user_ids


class AttachmentMixin(RichFieldsMixin):
    class Meta:
        abstract = True

    attachments = GenericRelation(Attachment, object_id_field='attached_object_id', content_type_field='attached_content_type')

    def save(self, *args, **kwargs):
        super(AttachmentMixin, self).save(*args, **kwargs)
        self.update_attachments_links()

    def attachments_in_fields(self):
        """ Can be overridden in parent Model """
        return Attachment.objects.none()

    def get_rich_fields(self):
        yield from self.rich_fields
        yield from self.revision_rich_fields()

    def revision_rich_fields(self):
        if hasattr(self, 'has_revisions') and self.has_revisions():
            for revision in self.revision_set.all():
                yield from revision.rich_fields

    def attachments_in_text(self):
        sources = set()
        for tiptap in self.get_rich_fields():
            parser = Tiptap(tiptap)
            sources.update(parser.attached_sources)

        attachments = self.sources_to_attachments(sources)

        return attachments

    def update_attachments_links(self):
        attachments_found = self.attachments_in_text()
        attachments_found = attachments_found.union(self.attachments_in_fields())

        current = self.attachments.get_queryset()

        new = attachments_found.difference(current)
        removed = current.difference(attachments_found)

        for x in new:
            x.attached = self
            x.save()

        for x in removed:
            x.delete()

    def source_to_attachment_id(self, source):
        # NOTE: this is a simple approach that fits the current urls "/attachment/<type>/<id>", it might not be sufficient for future changes
        source_parts = PurePosixPath(unquote(urlparse(source).path)).parts
        if len(source_parts) < 2:
            return None

        if not source_parts[1] == 'attachment':
            return None

        if not is_valid_uuid(source_parts[-1]):
            return None

        return source_parts[-1]

    def sources_to_attachments(self, sources):
        attachment_ids = filter(None, [self.source_to_attachment_id(source) for source in sources])
        return Attachment.objects.filter(id__in=attachment_ids)

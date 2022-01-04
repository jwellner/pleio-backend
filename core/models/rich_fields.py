import abc
from core.models.attachment import Attachment
from core.models.shared import AbstractModelMeta
from core.utils.tiptap_parser import Tiptap
from django.contrib.contenttypes.fields import GenericRelation
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from .mixin import NotificationMixin

class RichFieldsMixin(metaclass=AbstractModelMeta):
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

class AttachmentMixin(RichFieldsMixin, metaclass=AbstractModelMeta):
    class Meta:
        abstract = True

    attachments = GenericRelation(Attachment, object_id_field='attached_object_id', content_type_field='attached_content_type')

    def attachments_in_text(self):
        sources = set()
        for tiptap in self.rich_fields:
            parser = Tiptap(tiptap)
            sources.update(parser.attached_sources)

        return self.sources_to_attachments(sources)

    def update_attachments_links(self):
        from_text = self.attachments_in_text()
        current = self.attachments.get_queryset()

        new = from_text.difference(current)
        removed = current.difference(from_text)

        for x in new:
            x.attached = self
            x.save()

        for x in removed:
            x.delete()

    def source_to_attachment_id(self, source):
        # NOTE: this is a simple approach that fits the current urls "/attachment/<type>/<id>", it might not be sufficient for future changes
        source_parts = PurePosixPath(unquote(urlparse(source).path)).parts
        # NOTE: Images that have been added with addImage end up in "/file/download/<id>/<name>" these are filefolders so they are skipped
        if source_parts[1] == 'file':
            return None

        return source_parts[-1]

    def sources_to_attachments(self, sources):
        attachment_ids = filter(None, [self.source_to_attachment_id(source) for source in sources])
        return Attachment.objects.filter(id__in=attachment_ids)

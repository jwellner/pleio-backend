import abc
import json

from django.contrib.contenttypes.fields import GenericRelation
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from core.models.attachment import Attachment
from core.models.shared import AbstractModel
from core.utils.tiptap_parser import Tiptap
from core.lib import is_valid_uuid, get_model_name, tenant_schema

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

    def save(self, *args, **kwargs):
        super(MentionMixin, self).save(*args, **kwargs)
        self.send_notifications()

    def send_notifications(self):
        """ Look for users that are mentioned and notify them """
        # extra robustness for when tests don't assign an owner also don't send as deleted user
        # also don't try to create notifications when user is inactive
        if not self.owner or not self.owner.is_active:
            return

        if self.mentioned_users:
            from core.tasks import create_notification  # prevent circular import
            create_notification.delay(tenant_schema(), 'mentioned', get_model_name(self), self.id, self.owner.id)


class ReplaceAttachments:
    def __init__(self):
        self.attachment_map = {}

    def append(self, original_id, new_id):
        self.attachment_map[original_id] = new_id

    def replace(self, value):
        tiptap = Tiptap(value)
        for attachment, new_attachment in self.attachment_map:
            original = "/attachment/%s" % attachment
            replacement = "/attachment/%s" % new_attachment
            tiptap.replace_url(original, replacement)
            tiptap.replace_src(original, replacement)
        return json.dumps(tiptap.tiptap_json)

    def has_attachment(self, attachment_id):
        return attachment_id in self.attachment_map

    def translate(self, attachment_id):
        return self.attachment_map[attachment_id]


class AttachmentMixin(RichFieldsMixin):
    class Meta:
        abstract = True

    attachments = GenericRelation('core.Attachment', object_id_field='attached_object_id', content_type_field='attached_content_type')

    def save(self, *args, **kwargs):
        super(AttachmentMixin, self).save(*args, **kwargs)
        self.update_attachments_links()

    def lookup_attachments(self):
        yield from TipTapAttachments(*self.rich_fields).attachments()
        yield from self.revision_attachments()

    def revision_attachments(self):
        if hasattr(self, 'has_revisions') and self.has_revisions():
            for revision in self.revision_set.all():
                yield from TipTapAttachments(*revision.rich_fields).attachments()

    def update_attachments_links(self):
        attachments_found = Attachment.objects.filter(id__in=[*self.lookup_attachments()])

        current = self.attachments.get_queryset()

        new = attachments_found.difference(current)
        removed = current.difference(attachments_found)

        for x in new:
            x.attached = self
            x.save()

        for x in removed:
            x.delete()

    def replace_attachments(self, attachment_map: ReplaceAttachments):
        if hasattr(self, 'rich_description') and getattr(self, 'rich_description'):
            setattr(self, 'rich_description', attachment_map.replace(self.rich_description))


class TipTapAttachments:
    def __init__(self, *fields):
        self.fields = fields

    def attachments(self):
        for field in self.fields:
            yield from self.attachments_in_text(field)

    def attachments_in_text(self, field):
        sources = set()
        parser = Tiptap(field)
        sources.update(parser.attached_sources)

        yield from self.sources_to_attachment_ids(sources)

    def sources_to_attachment_ids(self, sources):
        for source in sources:
            # NOTE: this is a simple approach that fits the current urls "/attachment/<type>/<id>", it might not be sufficient for future changes
            source_parts = PurePosixPath(unquote(urlparse(source).path)).parts
            if len(source_parts) < 2:
                continue

            if not source_parts[1] == 'attachment':
                continue

            if not is_valid_uuid(source_parts[-1]):
                continue

            yield source_parts[-1]

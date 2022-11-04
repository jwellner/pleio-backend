import logging
from django.db.models.signals import post_delete
from core.models.mixin import ModelWithFile

logger = logging.getLogger(__name__)

def file_delete_handler(sender, instance, using, **kwargs):
    # pylint: disable=unused-argument
    instance.delete_files()


# When deleting GenericRelated models the delete method is not called. But the post_delete signal is working.
# Example: Blog with attachments is deleted and the attachment.delete is not called but post_delete signal is...
# https://github.com/django/django/blob/5e0aa362d91d000984995ce374c2d7547d8d107f/django/contrib/contenttypes/fields.py#L701
for subclass in ModelWithFile.__subclasses__():
    post_delete.connect(file_delete_handler, subclass)

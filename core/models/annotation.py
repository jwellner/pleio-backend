import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class AnnotationManager(models.Manager):
    def get_for(self, user, content_object, key, **kwargs):
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            return self.get(key=key, content_type=content_type,
                object_id=content_object.pk, user=user, **kwargs)
        except self.model.DoesNotExist:
            return None

    def get_all_for(self, content_object, key, **kwargs):
        content_type = ContentType.objects.get_for_model(content_object)
        return self.filter(key=key, content_type=content_type, object_id=content_object.pk, **kwargs)

    def add(self, user, content_object, key):
        return self.create(user=user, content_object=content_object, key=key)

class Annotation(models.Model):
    """
    Annotate content with user data
    """
    ANNOTATION_TYPES = (
        ('bookmarked', 'Bookmarked'),
        ('voted', 'Voted'),
        ('followed', 'Followed')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4)
    content_object = GenericForeignKey('content_type', 'object_id')

    key = models.CharField(
        max_length=16,
        choices=ANNOTATION_TYPES,
        default='bookmarked'
    )

    data = models.JSONField(null=True, blank=True)

    user = models.ForeignKey('user.User', on_delete=models.CASCADE)

    created_at = models.DateTimeField(default=timezone.now)

    objects = AnnotationManager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('content_type', 'object_id', 'user', 'key')

    def __str__(self):
        return u'%s %s %s' % (self.user, self.key, self.content_object)

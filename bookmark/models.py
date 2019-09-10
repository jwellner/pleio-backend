import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import User

class BookmarksManager(models.Manager):
    def get_for(self, content_object, key, **kwargs):
        """
        Return the instance related to *content_object* and matching *kwargs*. 
        Return None if a bookmark is not found.
        """
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            return self.get(key=key, content_type=content_type, 
                object_id=content_object.pk, **kwargs)
        except self.model.DoesNotExist:
            return None

    def add(self, user, content_object, key):
        """
        Add a bookmark, given the user, the model instance and the key.
        
        Raise a *Bookmark.AlreadyExists* exception if that kind of 
        bookmark is present in the db.
        """
        return self.create(user=user, content_object=content_object, key=key)

class Bookmark(models.Model):

    BOOKMARK_TYPES = (
        ('bookmark', 'Bookmark'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    key = models.CharField(
        max_length=16,
        choices=BOOKMARK_TYPES,
        default='bookmark'
    )

    user = models.ForeignKey(User, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = BookmarksManager()
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'key', 'user')

    def __str__(self):
        return u'Bookmark for %s by %s' % (self.content_object, self.user)

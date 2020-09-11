import uuid
from django.db import models
from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from notifications.models import Notification

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

class VoteMixin(models.Model):
    def vote_count(self):

        result = Annotation.objects.get_all_for(content_object=self, key="voted").annotate(
            score=Cast(KeyTextTransform('score', 'data'), IntegerField())
        ).aggregate(Sum("score"))

        count = result.get("score__sum")

        if count:
            return count

        return 0

    def has_voted(self, user):
        if not user.is_authenticated:
            return False

        vote = Annotation.objects.get_for(content_object=self, key="voted", user=user)

        if vote:
            return True

        return False

    def can_vote(self, user):
        if not user.is_authenticated:
            return False

        return True

    def get_vote(self, user):
        if not user.is_authenticated:
            return None

        return Annotation.objects.get_for(content_object=self, key="voted", user=user)

    def add_vote(self, user, score):
        if not user.is_authenticated:
            return None

        if score in [-1,1]:
            return Annotation.objects.create(
                user=user,
                content_object=self,
                key="voted",
                data={"score": score}
            )

        return None

    def remove_vote(self, user):
        if user.is_authenticated:
            vote = Annotation.objects.get_for(content_object=self, key="voted", user=user)

            if vote:
                vote.delete()

    class Meta:
        abstract = True

class BookmarkMixin(models.Model):
    """
    BookmarkMixin add to model to implement Bookmarks
    """
    class Meta:
        abstract = True

    def can_bookmark(self, user):
        if not user.is_authenticated:
            return False

        return True

    def is_bookmarked(self, user):
        if user.is_authenticated:
            isBookmarked = Annotation.objects.get_for(content_object=self, key='bookmarked', user=user)
            if isBookmarked:
                return True

        return False

    def get_bookmark(self, user):
        if not user.is_authenticated:
            return None

        return Annotation.objects.get_for(content_object=self, key="bookmarked", user=user)

    def add_bookmark(self, user):
        if not user.is_authenticated:
            return None

        return Annotation.objects.create(
            user=user,
            content_object=self,
            key="bookmarked"
        )

    def remove_bookmark(self, user):
        if user.is_authenticated:
            vote = Annotation.objects.get_for(content_object=self, key="bookmarked", user=user)

            if vote:
                vote.delete()

class FollowMixin(models.Model):
    """
    FollowMixin add to model to implement Follow
    """
    class Meta:
        abstract = True

    def can_follow(self, user):
        if not user.is_authenticated:
            return False

        return True

    def is_following(self, user):
        if user.is_authenticated:
            isFollowing = Annotation.objects.get_for(content_object=self, key='followed', user=user)
            if isFollowing:
                return True

        return False

    def get_follow(self, user):
        if not user.is_authenticated:
            return None

        return Annotation.objects.get_for(content_object=self, key="followed", user=user)

    def add_follow(self, user):
        if not user.is_authenticated:
            return None

        return Annotation.objects.create(
            user=user,
            content_object=self,
            key="followed"
        )

    def remove_follow(self, user):
        if user.is_authenticated:
            vote = Annotation.objects.get_for(content_object=self, key="followed", user=user)

            if vote:
                vote.delete()

class NotificationMixin(models.Model):
    """
    NotificationMixin add to model to implement notification on 'created'
    """
    class Meta:
        abstract = True

    _notification_action = GenericRelation(
        Notification,
        content_type_field='action_object_content_type',
        object_id_field='action_object_object_id'
    )
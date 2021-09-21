from django.db import models
from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from notifications.models import Notification
from .annotation import Annotation

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

    def followers(self):
        users = [i.user for i in Annotation.objects.get_all_for(content_object=self, key="followed")]
        return users
        

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

class FeaturedCoverMixin(models.Model):
    """
    FeaturedCoverMixin add to model to implement featured cover fields
    """
    class Meta:
        abstract = True

    featured_image = models.ForeignKey(
        "file.FileFolder",
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.TextField(null=True, blank=True)
    featured_video_title = models.CharField(max_length=256, default="")
    featured_position_y = models.IntegerField(default=0, null=False)
    featured_alt = models.CharField(max_length=256, default="")

    @property
    def featured_image_url(self):
        if self.featured_image:
            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(self.featured_image.updated_at.timestamp()))
        return None
import abc

from django.apps import apps
from django.db import models
from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.text import slugify
from notifications.models import Notification

from .annotation import Annotation
from core.models.shared import AbstractModel
from core.utils.convert import truncate_rich_description, tiptap_to_text, tiptap_to_html
from core.lib import delete_attached_file
from core.constances import USER_ROLES


class TitleMixin(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(max_length=256)

    @property
    def slug(self):
        return slugify(self.title)


class HasMediaMixin:

    def get_media_status(self):
        raise NotImplementedError()

    def get_media_filename(self):
        raise NotImplementedError()

    def get_media_content(self):
        raise NotImplementedError()


class RichDescriptionMediaMixin(HasMediaMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert hasattr(self, 'rich_description'), "Expected a rich_description field for export entity as media"

    def get_media_status(self):
        return bool(self.rich_description)

    def get_media_filename(self):
        if isinstance(self, TitleMixin):
            return "{slug}.html".format(slug=self.slug)
        raise NotImplementedError()

    def get_media_content(self):
        return tiptap_to_html(self.rich_description)


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

        if score in [-1, 1]:
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

        annotation = Annotation.objects.get_for(
            user,
            self,
            'followed',
        )
        if not annotation:
            annotation = Annotation.objects.create(
                user=user,
                content_object=self,
                key='followed',
            )

        return annotation

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


class ArticleMixin(models.Model):
    class Meta:
        abstract = True

    abstract = models.TextField(null=True, blank=True)
    rich_description = models.TextField(null=True, blank=True)

    @property
    def excerpt(self):
        if self.abstract:
            return self.abstract

        return truncate_rich_description(self.rich_description)

    @property
    def description(self):
        return tiptap_to_text(self.rich_description)


class ModelWithFile(AbstractModel):
    class Meta:
        abstract = True

    @property
    @abc.abstractmethod
    def file_fields(self):
        """ Return a list of fields that contain a file (i.e. FileField and ImageField) """

    def delete(self, *args, **kwargs):
        self.delete_files()
        super(ModelWithFile, self).delete(*args, **kwargs)

    def delete_files(self):
        for field in self.file_fields:
            delete_attached_file(field)


class CommentMixin(models.Model):
    comments = GenericRelation('core.Comment')

    def can_comment(self, user):
        if not user.is_authenticated:
            return False

        if isinstance(self, apps.get_model('core', 'Comment')) and \
                isinstance(self.container, apps.get_model('core', 'Comment')):
            return False

        if self.group and not self.group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
            return False

        return True

    def get_flat_comment_list(self, comments=None):
        if not comments:
            comments = self.comments.all()
        for item in comments:
            yield item
            if item.comments.count() > 0:
                for x in self.get_flat_comment_list(item.comments.all()):
                    yield x

    class Meta:
        abstract = True


class RevisionMixin(models.Model):
    class Meta:
        abstract = True

    def last_revision(self):
        # pylint: disable=import-outside-toplevel
        from core.models import Revision
        revisions = Revision.objects.get_queryset()
        revisions = revisions.filter(_container=self.guid)
        return revisions.latest('created_at')


def default_featured_image_properties(entity):
    return {
        "image": entity.featured_image.guid if entity.featured_image else None,
        "video": entity.featured_video,
        "position_y": entity.featured_position_y,
        "title": entity.featured_video_title,
        "alt": entity.featured_alt,
    }

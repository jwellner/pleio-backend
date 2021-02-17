from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, Comment, NotificationMixin
from core.constances import USER_ROLES
from file.models import FileFolder


class Question(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, NotificationMixin):
    """
    Question
    """
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.TextField(null=True, blank=True)
    featured_position_y = models.IntegerField(default=0, null=False)
    featured_alt = models.CharField(max_length=256, default="")

    best_answer = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def can_close(self, user):
        if not user.is_authenticated:
            return False

        if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.QUESTION_MANAGER) or user == self.owner:
            return True

        return False


    def can_choose_best_answer(self, user):
        if not user.is_authenticated:
            return False

        if self.is_closed:
            return False

        if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.QUESTION_MANAGER) or user == self.owner:
            return True

        return False

    def __str__(self):
        return f"Question[{self.title}]"

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/questions/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()

    @property
    def type_to_string(self):
        return 'question'

    @property
    def featured_image_url(self):
        if self.featured_image:
            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(self.featured_image.updated_at.timestamp()))
        return None


auditlog.register(Question)
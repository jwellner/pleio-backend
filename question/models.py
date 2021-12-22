from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core import config
from core.lib import get_acl
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, Comment, MentionMixin, FeaturedCoverMixin, ArticleMixin
from core.constances import USER_ROLES


class Question(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, MentionMixin, FeaturedCoverMixin, ArticleMixin):
    """
    Question
    """
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    description = models.TextField(default="")
    rich_description = models.TextField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

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

        if (
            (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.QUESTION_MANAGER) or user == self.owner)
            and config.QUESTIONER_CAN_CHOOSE_BEST_ANSWER
        ):
            return True

        return False

    def can_write(self, user):
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return True

        if user.is_authenticated and self.group and self.group.members.filter(user=user, type__in=['admin', 'owner']).exists():
            return True

        if self.is_locked:
            return False

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def is_locked(self):
        if config.QUESTION_LOCK_AFTER_ACTIVITY and self.comments.count() > 0:
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
    def rich_fields(self):
        return [self.rich_description]


auditlog.register(Question)

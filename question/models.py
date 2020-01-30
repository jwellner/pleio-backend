from django.db import models
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, Comment

class Question(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin):
    """
    Question
    """
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    best_answer = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def can_close(self, user):
        if not user.is_authenticated:
            return False

        if user.is_admin or user == self.owner: # TODO: add question expert role
            return True

        return False


    def can_choose_best_answer(self, user):
        if not user.is_authenticated:
            return False

        if self.is_closed:
            return False

        if user.is_admin or user == self.owner:  # TODO: add question expert role
            return True

        return False

    def __str__(self):
        return self.title

    def type_to_string(self):
        return 'question'

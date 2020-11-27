from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin
from file.models import FileFolder
from core.constances import USER_ROLES
from core.lib import get_acl


class News(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin):
    """
    News
    """
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    
    is_featured = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.TextField(null=True, blank=True)
    featured_position_y = models.IntegerField(default=0, null=False)

    source = models.TextField(default="")

    def __str__(self):
        return self.title

    @property
    def type_to_string(self):
        return 'news'

    @property
    def url(self):
        return '/news/view/{}/{}'.format(
            self.guid, slugify(self.title)
        ).lower()

    @property
    def featured_image_url(self):
        if self.featured_image:
            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(self.featured_image.updated_at.timestamp()))
        return None

    def can_write(self, user):
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

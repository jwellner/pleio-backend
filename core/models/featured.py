from django.db import models
from django.urls import reverse


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

    def is_featured_changed(self, original):
        return self.serialize_featured() != original

    def serialize_featured(self):
        return {
            'video': self.featured_video,
            'videoTitle': self.featured_video_title,
            'image': self.featured_image.download_url if self.featured_image else None,
            'imageGuid': self.featured_image.guid if self.featured_image else None,
            'positionY': self.featured_position_y,
            'alt': self.featured_alt,
        }

    def is_featured_image_changed(self, original):
        content = self.serialize_featured()
        original_image = original['imageGuid'] or ''
        new_image = content['imageGuid'] or ''
        return original_image != new_image

    def unserialize_featured(self, data):
        from file.models import FileFolder
        self.featured_video = data.get('video', '')
        self.featured_video_title = data.get('videoTitle', '')
        self.featured_position_y = data.get('positionY', 0)
        self.featured_alt = data.get('alt', '')
        self.featured_image = FileFolder.objects.get(id=data['imageGuid']) if data.get('imageGuid') else None

    @property
    def featured_image_url(self):
        if self.featured_image:
            timestamp = self.featured_image.updated_at.timestamp()
            try:
                latest = self.featured_image.resized_images.latest('updated_at')
                timestamp = latest.updated_at.timestamp()
            except Exception:
                pass

            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(timestamp))
        return None

    @property
    def featured_image_guid(self):
        if self.featured_image:
            return self.featured_image.guid
        return None

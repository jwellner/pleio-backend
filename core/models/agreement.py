from django.db import models
from django.urls import reverse
from django.utils import timezone


class CustomAgreement(models.Model):
    class Meta:
        ordering = ['created_at']

    name = models.CharField(max_length=100, unique=True)
    document = models.FileField(upload_to='agreements')
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def url(self):
        return reverse('custom_agreement', args=[self.id])

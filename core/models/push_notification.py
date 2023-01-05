from django.db import models


class WebPushSubscription(models.Model):
    browser = models.CharField(max_length=100)
    endpoint = models.URLField(max_length=800)
    auth = models.CharField(max_length=100)
    p256dh = models.CharField(max_length=100)
    user = models.ForeignKey(
        'user.User',
        related_name='web_push_subscriptions',
        on_delete=models.PROTECT
    )

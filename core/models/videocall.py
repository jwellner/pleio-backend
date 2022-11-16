import uuid

from django.db import models
from django.template.loader import render_to_string

from core.lib import tenant_schema


class VideoCall(models.Model):
    class Meta:
        ordering = ['created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    host_url = models.URLField(null=False)
    guest_url = models.URLField(null=False)

    def recipients(self):
        return [self.user]

    def custom_message(self):
        guest_list, guest = self.guests.guest_list()
        if guest:
            return render_to_string("notification/videocall_host_notification.html", {
                'name': self.user.name,
                'guest_list': ', '.join([g.name for g in guest_list]),
                'guest': guest.name,
                'url': self.host_url
            })
        return ''

    @property
    def guid(self):
        return str(self.id)

    def send_notification(self):
        from core.tasks import create_notification
        create_notification.delay(
            schema_name=tenant_schema(),
            verb="custom",
            model_name=self._meta.label,
            entity_id=self.guid,
            sender_id=self.user.guid
        )


class VideoCallGuestQueryset(models.QuerySet):

    def guest_list(self):
        guest_list = []
        for vc_guest in self.all():
            guest_list.append(vc_guest.user)
        size = len(guest_list)
        if size > 1:
            return guest_list[:-1], guest_list[size - 1]
        return [], guest_list[0]


class VideoCallGuest(models.Model):
    class Meta:
        ordering = ['created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    video_call = models.ForeignKey('core.VideoCall', on_delete=models.CASCADE, related_name="guests")
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="guests")

    objects = VideoCallGuestQueryset.as_manager()

    def recipients(self):
        return [self.user]

    def custom_message(self):
        return render_to_string("notification/videocall_guest_notification.html", {
            "name": self.video_call.user.name,
            "url": self.video_call.guest_url,
        })

    @property
    def host(self):
        return self.video_call.user

    @property
    def guid(self):
        return str(self.id)

    def send_notification(self):
        from core.tasks import create_notification
        create_notification.delay(
            schema_name=tenant_schema(),
            verb="custom",
            model_name=self._meta.label,
            entity_id=self.guid,
            sender_id=self.video_call.user.guid
        )

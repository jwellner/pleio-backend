from activity.models import StatusUpdate
from blog.models import Blog
from core import config
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from notifications.models import Notification
from core.models.group import Group

from core.services.mail_service import MailService, MailTypeEnum
from user.models import User

class MailServiceTestCase(FastTenantTestCase):

    def setUp(self):
        self.mail_service = MailService(MailTypeEnum.DIRECT)
        self.sender = mixer.blend(User)

    def test_get_notification_subject_single(self):
        entity = mixer.blend(Blog)
        notification =  mixer.blend(
            Notification,
            actor_object_id=self.sender.id,
            action_object=entity,
        )

        subject = self.mail_service.get_notification_subject([notification])

        self.assertEqual(f"Notificatie op {entity.title}", subject)

    def test_get_notification_subject_plural(self):
        entity = mixer.blend(Blog)
        notification1 =  mixer.blend(
            Notification,
            actor_object_id=self.sender.id,
            action_object=entity,
        )
        notification2 =  mixer.blend(
            Notification,
            actor_object_id=self.sender.id,
            action_object=entity,
        )

        subject = self.mail_service.get_notification_subject([notification1, notification2])

        self.assertEqual(f"Nieuwe notificaties op {config.NAME}", subject)

    def test_get_notification_single_without_title(self):
        group = mixer.blend(Group)
        entity = mixer.blend(StatusUpdate, title="", group=group)
        notification = mixer.blend(
            Notification,
            actor_object_id=self.sender.id,
            action_object=entity
        )

        subject = self.mail_service.get_notification_subject([notification])

        self.assertEqual(f"Notificatie op statusupdate in groep {entity.group.name}", subject)

    def test_get_notification_single_without_title_and_group(self):
        entity = mixer.blend(StatusUpdate, title="", group=None)
        notification = mixer.blend(
            Notification,
            actor_object_id=self.sender.id,
            action_object=entity
        )

        subject = self.mail_service.get_notification_subject([notification])

        self.assertEqual(f"Notificatie op statusupdate", subject)

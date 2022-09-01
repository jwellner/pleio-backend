from datetime import datetime, timedelta

from django.core.signing import Signer, TimestampSigner
from django.urls import reverse
from django.utils.timezone import localtime

SECONDS_THRESHOLD = 360000


class UnsubscribeTokenizer():
    TYPE_NOTIFICATIONS = 'notifications'
    TYPE_OVERVIEW = 'overview'

    def __init__(self):
        # Though we store a timestamp, unpacking must always work. So we don't use a timestamp signer.
        self.signer = Signer()

    def pack(self, user, mail_type):
        return self.signer.sign_object([user.email, mail_type, localtime().timestamp()], compress=True)

    def unpack(self, data):
        from user.models import User
        result = self.signer.unsign_object(data)
        timestamp = datetime.fromtimestamp(result[2])
        due_date = datetime.now() - timedelta(seconds=SECONDS_THRESHOLD)
        return (User.objects.get(email=result[0]),
                result[1],
                timestamp < due_date)

    def create_url(self, user, mail_type):
        return reverse("unsubscribe", args=[self.pack(user, mail_type)])


class EmailSettingsTokenizer():

    def __init__(self):
        self.signer = TimestampSigner()

    def pack(self, user):
        return self.signer.sign_object({
            'id': user.guid,
            'email': user.email
        }, compress=True)

    def unpack(self, token):
        from user.models import User
        data = self.signer.unsign_object(token, max_age=SECONDS_THRESHOLD)
        return User.objects.get(id=data['id'], email=data['email'])

    def create_url(self, user):
        return reverse("edit_email_settings", args=[self.pack(user)])

from user.models import User


class MailerBase:

    @staticmethod
    def ignore_email(email):
        return User.objects.filter(is_active=False, email=email).exists()

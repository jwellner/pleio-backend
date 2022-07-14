import faker

from core.mail_builders.base import MailerBase


class InvalidMailerSubclass():
    pass


class ValidMailerSubclass(MailerBase):

    def __init__(self, **kwargs):
        kwargs.setdefault('receiver_email', faker.Faker().email())
        kwargs.setdefault('subject', faker.Faker().sentence())
        kwargs.setdefault('receiver', None)
        kwargs.setdefault('sender', None)
        super(ValidMailerSubclass, self).__init__(**kwargs)

    def send(self):
        pass

    def get_receiver(self):
        return self.kwargs['receiver']

    def get_receiver_email(self):
        return self.kwargs['receiver_email']

    def get_sender(self):
        return self.kwargs['sender']

    def get_subject(self):
        return self.kwargs['subject']

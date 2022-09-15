from django.utils.translation import gettext as _

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.convert import tiptap_to_html
from core.utils.entity import load_entity_by_id


def schedule_comment_without_account_mail(comment_request, entity):
    from core.models import MailInstance
    MailInstance.objects.submit(CommentWithoutAccountMailer,
                                mailer_kwargs={
                                    'comment_request': comment_request.pk,
                                    'entity': entity.guid,
                                })


class CommentWithoutAccountMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        from core.models import CommentRequest
        self.comment_request: CommentRequest = CommentRequest.objects.get(pk=kwargs['comment_request'])
        self.entity = load_entity_by_id(kwargs['entity'], ['core.Entity'])
        super().__init__(**kwargs)

    def get_context(self):
        context = self.build_context()
        context['confirm_url'] = get_full_url(f"/comment/confirm/{self.entity.guid}?email={self.get_receiver_email()}&code={self.comment_request.code}")
        context['comment'] = tiptap_to_html(self.comment_request.rich_description)
        context['entity_title'] = self.entity.title
        context['entity_url'] = get_full_url(self.entity.url)
        return context

    def get_language(self):
        return config.LANGUAGE

    def get_template(self):
        return 'email/confirm_add_comment_without_account.html'

    def get_receiver(self):
        return None

    def get_receiver_email(self):
        return self.comment_request.email

    def get_sender(self):
        return None

    def get_subject(self):
        return _("Confirm comment on %(site_name)s") % {'site_name': config.NAME}

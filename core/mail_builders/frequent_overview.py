from django.db.models import Q
from django.utils.timezone import timedelta, localtime
from django.utils.translation import gettext as _

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id
from core.utils.mail import UnsubscribeTokenizer


def schedule_frequent_overview_mail(user, interval):
    from core.models import MailInstance
    MailInstance.objects.submit(FrequentOverviewMailer, {
        'user': user.guid,
        'interval': interval,
    })


class FrequentOverviewMailer(TemplateMailerBase):

    _unsubscribe_url = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User'])
        self.interval = kwargs['interval']

    def get_context(self):
        collection = EntityCollection(self.user, self.interval)

        # do not send mail when there are now new notifications
        if not collection.has_content():
            raise self.FailSilentlyError()

        context = self.build_context(user=self.user)
        context['entities'] = self.serialize_entities(collection.get_entities())
        context['featured'] = self.serialize_entities(collection.get_featured())
        context['intro_text'] = config.EMAIL_OVERVIEW_INTRO
        context['title'] = config.EMAIL_OVERVIEW_TITLE
        context['featured_enabled'] = config.EMAIL_OVERVIEW_ENABLE_FEATURED
        context['featured_title'] = config.EMAIL_OVERVIEW_FEATURED_TITLE
        context['subject'] = self.get_subject()
        context['unsubscribe_url'] = self.unsubscribe_url
        return context

    def get_headers(self):
        headers = super().get_headers()
        headers['List-Unsubscribe'] = self.unsubscribe_url
        return headers

    @property
    def unsubscribe_url(self):
        if not self._unsubscribe_url:
            tokenizer = UnsubscribeTokenizer()
            url = tokenizer.create_url(self.user, tokenizer.TYPE_OVERVIEW)
            self._unsubscribe_url = get_full_url(url)
        return self._unsubscribe_url

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return "email/send_overview_emails.html"

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return None

    def get_subject(self):
        return config.EMAIL_OVERVIEW_SUBJECT or _("Regular overview of %(site_name)s") % {'site_name': config.NAME}

    def send(self):
        super().send()
        self.user.profile.overview_email_last_received = localtime()
        self.user.profile.save()

    @staticmethod
    def serialize_entities(entities):
        serializable_entities = []

        for entity in entities:
            try:
                featured_image_url = entity.featured_image_url
            except Exception:
                featured_image_url = None
            entity_group = False
            entity_group_name = ""
            entity_group_url = ""
            if entity.group:
                entity_group = True
                entity_group_name = entity.group.name
                entity_group_url = entity.group.url

            serializable_entity = {
                'type_to_string': entity.type_to_string,
                'featured_image_url': featured_image_url,
                'title': entity.title,
                'description': entity.description,
                'owner_name': entity.owner.name,
                'url': entity.url,
                'group': entity_group,
                'group_name': entity_group_name,
                'group_url': entity_group_url,
                'published': entity.published.strftime("%e-%m-%Y")  # formatting done here because it's not a date object anymore after serialization
            }
            serializable_entities.append(serializable_entity)

        return serializable_entities


class EntityCollection:
    _is_processed = False
    _entities = None
    _featured = None
    MAX_FEATURED = 3
    MAX_ENTITIES = 5

    def __init__(self, user, interval):
        self.user = user
        self.interval = interval

    def has_content(self):
        if self.get_entities() or self.get_featured():
            return True
        return False

    def get_entities(self):
        self._process()
        return self._entities

    def get_featured(self):
        self._process()
        return self._featured

    def _process(self):
        if self._is_processed:
            return

        lower_bound = self._get_lower_bound()

        self._featured = self._process_featured(lower_bound
                                                )[:self.MAX_FEATURED]
        self._entities = self._process_entities(lower_bound, featured=self._featured
                                                )[:self.MAX_ENTITIES]

        self._is_processed = True

    def _get_lower_bound(self):
        # if user has never received overview mails use last interval period for time delta
        delta = self._get_delta()
        time_threshold = localtime() - delta
        last_occassion = self.user.profile.overview_email_last_received
        if last_occassion and last_occassion > time_threshold:
            return last_occassion
        return time_threshold

    def _get_delta(self):
        if self.interval == "monthly":
            return timedelta(weeks=4)
        if self.interval == "weekly":
            return timedelta(weeks=1)
        return timedelta(days=1)

    def _process_featured(self, since):
        from core.models import Entity
        if self.interval == 'monthly' or not config.EMAIL_OVERVIEW_ENABLE_FEATURED:
            return []

        featured_entities = Entity.objects.visible(self.user)
        featured_entities = featured_entities.filter(Q(is_recommended=True) | Q(is_featured=True))
        featured_entities = featured_entities.filter(published__gte=since)
        featured_entities = featured_entities.select_subclasses()
        return featured_entities

    def _process_entities(self, since, featured):
        from core.models import Entity

        entities = Entity.objects.visible(self.user)

        # filter on published after last received overview or maximum lower bound
        entities = self._filter_valid_content_type(entities)
        entities = self._exclude_viewed_content(entities)
        entities = self._exclude_featured_content(entities, featured)
        entities = entities.filter(published__gte=since)
        entities = entities.select_subclasses()
        entities = entities.order_by("-published")

        return self._tags_on_top(entities)

    @staticmethod
    def _filter_valid_content_type(qs):
        # pylint: disable=unsupported-binary-operation
        return qs.filter(
            ~Q(news__isnull=True) |
            ~Q(blog__isnull=True) |
            ~Q(event__isnull=True) |
            ~Q(wiki__isnull=True) |
            ~Q(question__isnull=True)
        )

    def _exclude_viewed_content(self, qs):
        from core.models import EntityView
        entity_views = EntityView.objects.filter(viewer=self.user)
        return qs.exclude(
            id__in=entity_views.values_list('entity_id', flat=True)
        )

    @staticmethod
    def _exclude_featured_content(qs, featured):
        if config.EMAIL_OVERVIEW_ENABLE_FEATURED:
            return qs.exclude(
                id__in=[e.guid for e in featured]
            )
        return qs

    def _tags_on_top(self, qs):
        from core.models import Tag
        tags = list(Tag.translate_tags(self.user.profile.overview_email_tags))

        # entities with user preferred tags are first in email
        selected_entities = list(qs.filter(_tag_summary__overlap=tags))
        selected_entities.extend(
            list(qs.exclude(_tag_summary__overlap=tags))
        )
        return selected_entities

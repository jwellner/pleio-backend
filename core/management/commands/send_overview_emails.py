from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone, dateformat, formats, translation
from django.utils.translation import ugettext_lazy
from django.conf import settings
from core import config
from core.lib import get_base_url, get_default_email_context
from core.models import Entity, EntityView
from datetime import timedelta
from django.db import connection
from tenants.models import Client
from user.models import User
from core.tasks import send_mail_multi
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder


def get_serializable_entities(entities):
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


class Command(BaseCommand):
    help = 'Send overview emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', dest='interval', required=True, choices=['daily', 'weekly', 'monthly'],
            help='interval of overview emails(daily, weekly, or monthly)',
        )

    def send_overview(self, user, entities, featured_entities, subject):
        if entities or featured_entities:
            context = get_default_email_context(user)
            context['entities'] = get_serializable_entities(entities)
            context['featured'] = get_serializable_entities(featured_entities)
            context['intro_text'] = config.EMAIL_OVERVIEW_INTRO
            context['title'] = config.EMAIL_OVERVIEW_TITLE
            context['featured_enabled'] = config.EMAIL_OVERVIEW_ENABLE_FEATURED
            context['featured_title'] = config.EMAIL_OVERVIEW_FEATURED_TITLE
            context['subject'] = subject

            send_mail_multi.delay(connection.schema_name, subject, 'email/send_overview_emails.html', context, user.email)
            user.profile.overview_email_last_received = timezone.now()
            user.profile.save()

    def handle(self, *args, **options):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)

        if connection.schema_name == 'public':
            return

        interval = options['interval']

        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True, _profile__overview_email_interval=interval)

        subject = config.EMAIL_OVERVIEW_SUBJECT
        for user in users:
            translation.activate(user.get_language())

            if not subject:
                subject = ugettext_lazy("Regular overview of %(site_name)s") % {'site_name': config.NAME}

            # determine lower bound of emails in queries
            # if user has never received overview mails use last interval period for time delta
            if interval == "monthly":
                delta = timedelta(weeks=4)
            elif interval == "weekly":
                delta = timedelta(weeks=1)
            else:
                delta = timedelta(days=1)

            time_threshold = timezone.now() - delta
            if user.profile.overview_email_last_received and user.profile.overview_email_last_received > time_threshold:
                lower_bound = user.profile.overview_email_last_received
            else:
                lower_bound = time_threshold

            featured_entities = Entity.objects.none()

            # do not sent featured items if interval is monthly
            if interval != 'monthly' and config.EMAIL_OVERVIEW_ENABLE_FEATURED:
                # get featured entities
                featured_entities = Entity.objects.visible(user)
                featured_entities = featured_entities.filter(Q(is_recommended=True) | Q(is_featured=True))
                featured_entities = featured_entities.filter(published__gte=lower_bound)
                featured_entities = featured_entities[:3]
                featured_entities = featured_entities.select_subclasses()

            # get the not featured entities
            entities = Entity.objects.visible(user)

            entity_views = EntityView.objects.filter(viewer=user)

            # filter on published after last received overview or maximum lower bound
            entities = entities.filter(published__gte=lower_bound)
            entities = entities.filter(
                ~Q(news__isnull=True) |
                ~Q(blog__isnull=True) |
                ~Q(event__isnull=True) |
                ~Q(wiki__isnull=True) |
                ~Q(question__isnull=True)
            ).order_by("-published")
            entity_views = entity_views.filter(created_at__gte=lower_bound)

            # remove featured and viewed entities from entities
            entities = entities.exclude(
                id__in=entity_views.values_list('entity_id', flat=True)
            )
            if config.EMAIL_OVERVIEW_ENABLE_FEATURED:
                entities = entities.exclude(
                    id__in=featured_entities.values_list('id', flat=True)
                )
            entities = entities.select_subclasses()

            # do not send mail when there are now new notifications
            if not entities and not featured_entities:
                continue

            # entities with user preferred tags are first in email
            selected_entities = list(entities.filter(tags__overlap=user.profile.overview_email_tags))
            selected_entities.extend(
                list(entities.exclude(tags__overlap=user.profile.overview_email_tags))
            )

            selected_entities = selected_entities[:5]

            self.send_overview(user, selected_entities, featured_entities, subject)

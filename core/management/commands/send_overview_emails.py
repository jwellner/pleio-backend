from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from core import config
from core.models import Entity, EntityView
from datetime import datetime, timedelta
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

    def send_overview(self, user, entities, featured_entities, subject, site_url):
        if entities or featured_entities:
            site_name = config.NAME
            user_url = site_url + '/user/' + user.guid + '/settings'
            primary_color = config.COLOR_PRIMARY

            entities = get_serializable_entities(entities)
            featured_entities = get_serializable_entities(featured_entities)

            context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                       'entities': entities, 'featured': featured_entities, 'intro_text': config.EMAIL_OVERVIEW_INTRO, 'title': config.EMAIL_OVERVIEW_TITLE,
                       'featured_enabled': config.EMAIL_OVERVIEW_ENABLE_FEATURED, 'featured_title': config.EMAIL_OVERVIEW_FEATURED_TITLE}
            send_mail_multi.delay(connection.schema_name, subject, 'email/send_overview_emails.html', context, user.email)
            user.profile.overview_email_last_received = datetime.now()
            user.profile.save()

    def handle(self, *args, **options):
        tenant = Client.objects.get(schema_name=connection.schema_name)

        site_url = 'https://' + tenant.domains.first().domain

        interval = options['interval']

        default_interval = config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY

        users = User.objects.filter(is_active=True)

        if config.EMAIL_OVERVIEW_SUBJECT:
            subject = config.EMAIL_OVERVIEW_SUBJECT
        else:
            subject = ugettext_lazy("Regular overview of %(site_name)s") % {'site_name': config.NAME}

        for user in users:

            # determine lower bound of emails in queries
            time_threshold = datetime.now() - timedelta(hours=1500)
            if user.profile.overview_email_last_received and user.profile.overview_email_last_received > time_threshold:
                lower_bound = user.profile.overview_email_last_received
            else:
                lower_bound = time_threshold


            # determine interval
            if not user.profile.overview_email_interval:
                overview_email_interval = default_interval
            else:
                overview_email_interval = user.profile.overview_email_interval

            if interval != overview_email_interval:
                continue

            # do not send mail to users that not logged in for 6 months
            if user.profile and user.profile.last_online and (user.profile.last_online < (datetime.now() - timedelta(hours=4460))):
                continue

            featured_entities = Entity.objects.none()

            # do not sent featured items if interval is monthly
            if overview_email_interval != 'monthly' and config.EMAIL_OVERVIEW_ENABLE_FEATURED:
                # get featured entities
                featured_entities = Entity.objects.visible(user)
                featured_entities = featured_entities.filter(Q(blog__is_recommended=True) | Q(blog__is_featured=True) | Q(news__is_featured=True))
                featured_entities = featured_entities.filter(created_at__gte=lower_bound)
                featured_entities = featured_entities[:3]
                featured_entities = featured_entities.select_subclasses()

            # get the not featured entities
            entities = Entity.objects.visible(user)

            entity_views = EntityView.objects.filter(viewer=user)

            # filter on created_at after last received overview or maximum lower bound
            entities = entities.filter(created_at__gte=lower_bound)
            entities = entities.filter(
                ~Q(news__isnull=True) |
                ~Q(blog__isnull=True) |
                ~Q(event__isnull=True) |
                ~Q(wiki__isnull=True) |
                ~Q(question__isnull=True)
            )
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

            self.send_overview(user, selected_entities, featured_entities, subject, site_url)

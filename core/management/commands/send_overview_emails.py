from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from core.lib import send_mail_multi, get_default_email_context
from core.models import Entity, EntityView
from user.models import User
from core import config
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Send overview emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url', dest='url', required=True,
            help='url in overview emails',
        )
        parser.add_argument(
            '--interval', dest='interval', required=True, choices=['daily', 'weekly', 'monthly'],
            help='interval of overview emails(daily, weekly, or monthly)',
        )

    def send_overview(self, user, entities, featured, subject, site_url):
        if entities:
            site_name = config.NAME
            user_url = site_url + '/user/' + user.guid + '/settings'
            primary_color = config.COLOR_PRIMARY
            context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                       'entities': entities, 'featured': featured, 'intro_text': config.EMAIL_OVERVIEW_INTRO, 'title': config.EMAIL_OVERVIEW_TITLE}
            email = send_mail_multi(subject, 'email/send_overview_emails.html', context, [user.email])
            email.send()
            user.profile.overview_email_last_received = datetime.now()
            user.profile.save()

    def handle(self, *args, **options):
        site_url = options['url']
        interval = options['interval']

        default_interval = config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY

        users = User.objects.filter(is_active=True)

        if config.EMAIL_OVERVIEW_SUBJECT:
            subject = config.EMAIL_OVERVIEW_SUBJECT
        else:
            subject = ugettext_lazy("Regular overview of %s" % config.NAME)

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
            if user.last_login and (user.last_login < datetime.now() - timedelta(hours=4460)):
                continue

            featured_entities = Entity.objects.none()

            # do not sent featured items if interval is monthly
            if overview_email_interval != 'monthly':
                # get featured entities
                featured_entities = Entity.objects.visible(user)
                featured_entities = featured_entities.filter(Q(blog__is_recommended=True) | Q(blog__is_featured=True) | Q(news__is_featured=True))

            # get the not featured entities
            entities = Entity.objects.visible(user)

            entity_views = EntityView.objects.filter(viewer=user)

            # filter on created_at after last received overview or maximum lower bound
            featured_entities = featured_entities.filter(created_at__gte=lower_bound)
            entities = entities.filter(created_at__gte=lower_bound)
            entity_views = entity_views.filter(created_at__gte=lower_bound)

            # remove featured and viewed entities from entities
            entities = entities.exclude(
                id__in=entity_views.values_list('entity_id', flat=True)
            ).exclude(
                id__in=featured_entities.values_list('id', flat=True)
            ).select_subclasses()

            # do not send mail when there are now new notifications
            if not entities and not featured_entities:
                continue

            featured_entities = featured_entities[:3]

            # entities with user preferred tags are first in email
            selected_entities = list(entities.filter(tags__overlap=user.profile.overview_email_tags))
            selected_entities.extend(
                list(entities.exclude(tags__overlap=user.profile.overview_email_tags))
            )

            selected_entities = selected_entities[:5]

            self.send_overview(user, selected_entities, featured_entities, subject, site_url)

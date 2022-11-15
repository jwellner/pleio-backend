from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django_tenants.utils import schema_context

from core import config
from core.utils.migrations.category_tags_reconstruct import reconstruct_tag_categories
from tenants.models import Client


@shared_task()
def report_is_tag_categories_consistent(reporter_email):
    report = []
    for client in Client.objects.exclude(schema_name='public'):
        try:
            with schema_context(client.schema_name):
                sure_categories = {}
                for item in config.TAG_CATEGORIES:
                    sure_categories[item['name']] = item['values']

                maybe_valid_tag_categories = reconstruct_tag_categories()

                for item in maybe_valid_tag_categories:
                    if item['name'] not in sure_categories:
                        if len(sure_categories) == 0:
                            report.append("%s: %s unexpectedly found in content. No TAG_CATEGORIES expected." % (client.schema_name, item['name']))
                        else:
                            report.append("%s: %s unexpectedly found in content. Expected one of %s." % (client.schema_name, item['name'],
                                                                                                         ", ".join(sure_categories.keys())))
                        continue
                    for tag in item['values']:
                        if tag not in sure_categories[item['name']]:
                            report.append("%s: Unexpectedly found %s.%s. Expected %s." % (
                                client.schema_name, item['name'], tag, ", ".join(sure_categories[item['name']]['values'])))
        except Exception as e:
            report.append("%s: Error during processing; %s.%s: %s" % (client.schema_name,
                                                                      e.__class__.__module__, e.__class__.__qualname__,
                                                                      str(e)))

    if reporter_email:
        if not report:
            report.append("Nothing to report")
        send_mail(subject="Report tag-category consistency",
                  message="\n".join(report),
                  from_email=settings.FROM_EMAIL,
                  recipient_list=[reporter_email],
                  fail_silently=False)

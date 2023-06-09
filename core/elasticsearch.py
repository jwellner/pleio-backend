import logging

from django.apps import apps
from django.db import models
from django.conf import settings
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import BaseSignalProcessor
from django_tenants.utils import parse_tenant_config_path
from elasticsearch.helpers import BulkIndexError
from elasticsearch_dsl import Index

from core.lib import tenant_schema

logger = logging.getLogger(__name__)


def log_elasticsearch_error(msg, e, instance, alternative_logger=None):
    _logger = alternative_logger or logger
    _logger.error("Elasticsearch error %s@%s: %s/%s %s/%s",
                  msg, tenant_schema(),
                  e.__class__.__qualname__, e,
                  instance.__class__.__name__, instance.pk)


class CustomSignalProcessor(BaseSignalProcessor):
    """Overwrites the default signal processor to not throw an error when elasticsearch fails to save.
    """

    def handle_save(self, sender, instance, **kwargs):
        """Overwrite default handle_save and stop raising exception on error
        """
        try:
            if isinstance(instance, apps.get_model('file.FileFolder')) and instance.group and not settings.ENV == 'test':
                schedule_index_document(instance)
            else:
                registry.update(instance)
                registry.update_related(instance)
        except Exception as e:
            retry_index_document(instance)
            log_elasticsearch_error('sending update task', e, instance)

    def handle_pre_delete(self, sender, instance, **kwargs):
        """Overwrite default handle_pre_delete and stop raising exception on error
        """
        try:
            registry.delete_related(instance)
        except Exception as e:
            log_elasticsearch_error('sending pre-delete task', e, instance)

    def handle_delete(self, sender, instance, **kwargs):
        """Overwrite default handle_pre_delete and stop raising exception on error
        """
        try:
            registry.delete(instance, raise_on_error=False)
        except Exception as e:
            if isinstance(e, BulkIndexError) and 'not_found' in str(e):
                return
            log_elasticsearch_error('sending delete task', e, instance)

    def setup(self):
        # Listen to all model saves.
        models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)

        # Use to manage related objects update
        models.signals.m2m_changed.connect(self.handle_m2m_changed)
        models.signals.pre_delete.connect(self.handle_pre_delete)

    def teardown(self):
        # Listen to all model saves.
        models.signals.post_save.disconnect(self.handle_save)
        models.signals.post_delete.disconnect(self.handle_delete)
        models.signals.m2m_changed.disconnect(self.handle_m2m_changed)
        models.signals.pre_delete.disconnect(self.handle_pre_delete)


def retry_index_document(instance):
    if settings.ENV == 'test':
        return
    instance = parent_or_self(instance)
    if instance.__class__ in registry.get_models():
        schedule_index_document(instance)


def parent_or_self(instance):
    try:
        return instance.index_instance()
    except AttributeError:
        pass
    return instance


def schedule_index_document(instance):
    # pylint: disable=import-outside-toplevel

    from core.tasks.elasticsearch_tasks import elasticsearch_index_document
    schema_name = parse_tenant_config_path("")
    elasticsearch_index_document.delay(schema_name, instance.id, instance.__class__.__name__)


def elasticsearch_status_report(index_name=None, report_on_alert=False):
    report = []
    for document_class in registry.get_documents():
        if not index_name or index_name == document_class.Index.name:
            document = document_class()
            expected = document.get_queryset().count()

            from elasticsearch_dsl import Search
            actual = Search(index=document_class.Index.name).filter('term', tenant_name=tenant_schema()).count()

            less_then_expected = bool(actual < .95 * expected)
            more_then_expected = bool(.95 * actual > expected)
            alert = less_then_expected or more_then_expected

            if alert or not report_on_alert:
                report.append({
                    "index": document.Index.name,
                    "expected": expected,
                    "actual": actual,
                    "alert": more_then_expected or less_then_expected
                })

    return sorted(report, key=lambda x: x['index'])

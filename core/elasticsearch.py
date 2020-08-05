import logging
from django.apps import apps
from django.db import models
from django.conf import settings
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import BaseSignalProcessor
from django_tenants.utils import parse_tenant_config_path
from core.tasks import elasticsearch_index_file

logger = logging.getLogger(__name__)

class CustomSignalProcessor(BaseSignalProcessor):
    """Overwrites the default signal processor to not throw an error when elasticsearch fails to save.
    """

    def handle_save(self, sender, instance, **kwargs):
        """Overwrite default handle_save and stop raising exception on error
        """
        try:
            if isinstance(instance, apps.get_model('file.FileFolder')) and instance.group:
                schema_name = parse_tenant_config_path("")
                elasticsearch_index_file.delay(schema_name, instance.id)
            else:
                registry.update(instance)
                registry.update_related(instance)

        except Exception as e:
            logger.error("Error sending update task: %s", e)

    def handle_pre_delete(self, sender, instance, **kwargs):
        """Overwrite default handle_pre_delete and stop raising exception on error
        """
        try:
            registry.delete_related(instance)
        except Exception as e:
            logger.error("Error updating elasticsearch: %s", e)

    def handle_delete(self, sender, instance, **kwargs):
        """Overwrite default handle_pre_delete and stop raising exception on error
        """
        try:
            registry.delete(instance, raise_on_error=False)
        except Exception as e:
            logger.error("Error updating elasticsearch: %s", e)

    def setup(self):
        if not settings.RUN_AS_ADMIN_APP:
            # Listen to all model saves.
            models.signals.post_save.connect(self.handle_save)
            models.signals.post_delete.connect(self.handle_delete)

            # Use to manage related objects update
            models.signals.m2m_changed.connect(self.handle_m2m_changed)
            models.signals.pre_delete.connect(self.handle_pre_delete)

    def teardown(self):
        if not settings.RUN_AS_ADMIN_APP:
            # Listen to all model saves.
            models.signals.post_save.disconnect(self.handle_save)
            models.signals.post_delete.disconnect(self.handle_delete)
            models.signals.m2m_changed.disconnect(self.handle_m2m_changed)
            models.signals.pre_delete.disconnect(self.handle_pre_delete)

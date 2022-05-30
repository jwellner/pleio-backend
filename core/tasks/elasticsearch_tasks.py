from celery import shared_task
from celery.utils.log import get_task_logger
from core.lib import get_model_by_subtype
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import schema_context
from elasticsearch_dsl import Search

from core.models import Group, Entity
from core.utils.entity import load_entity_by_id
from file.models import FileFolder
from tenants.models import Client
from user.models import User

logger = get_task_logger(__name__)

@shared_task(bind=True, ignore_result=True)
def elasticsearch_recreate_indices(self, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes, creates indexes
    '''
    if index_name:
        models = [get_model_by_subtype(index_name)]
    else:
        models = registry.get_models()

    # delete indexes
    for index in registry.get_indices(models):
        try:
            index.delete()
            logger.info('deleted index %s', index._name)
        except Exception:
            logger.info('index %s does not exist', index._name)

        try:
            index.create()
            logger.info('created index %s', index._name)
        except Exception:
            logger.info('index %s already exists', index._name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild_all(self, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes, creates indexes and populate tenants

    No option passed then all indices are rebuild
    Options: ['news', 'file', 'question' 'wiki', 'discussion', 'page', 'event', 'blog', 'user', 'group']

    '''
    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_rebuild.delay(client.schema_name, index_name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild(self, schema_name, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild search index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild \'%s\'', schema_name)

        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()

        for index in registry.get_indices(models):
            elasticsearch_repopulate_index_for_tenant.delay(schema_name, index._name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_repopulate_index_for_tenant(self, schema_name, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_repopulate_index_for_tenant \'%s\' \'%s\'', index_name, schema_name)

        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()

        for index in registry.get_indices(models):
            elasticsearch_delete_data_for_tenant(schema_name, index._name)

        for doc in registry.get_documents(models):
            logger.info("indexing %i '%s' objects",
                doc().get_queryset().count(),
                doc.django.model.__name__
            )
            qs = doc().get_indexing_queryset()

            if doc.django.model.__name__ == 'FileFolder':
                doc().update(qs, parallel=False, chunk_size=10)
            else:
                doc().update(qs, parallel=False, chunk_size=500)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_index_file(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    '''
    Index file for tenant
    '''
    with schema_context(schema_name):
        try:
            instance = FileFolder.objects.get(id=file_guid)
            registry.update(instance)
            registry.update_related(instance)

        except Exception as e:
            logger.error('elasticsearch_update %s %s: %s', schema_name, file_guid, e)


@shared_task()
def elasticsearch_index_document(schema_name, document_guid):
    with schema_context(schema_name):
        try:
            instance = load_entity_by_id(document_guid, [Group, Entity, User])
            registry.update(instance)
            registry.update_related(instance)
        except Exception as e:
            logger.error('elasticsearch_index_document %s %s: %s', schema_name, document_guid, e)

@shared_task()
def elasticsearch_delete_data_for_tenant(schema_name, index_name=None):
    # pylint: disable=protected-access
    '''
    Delete tenant data from elasticsearch
    '''
    if not schema_name:
        return

    logger.info('elasticsearch_delete_data_for_tenant \'%s\'', schema_name)

    if index_name:
        models = [get_model_by_subtype(index_name)]
    else:
        models = registry.get_models()

    for index in registry.get_indices(models):

        s = Search(index=index._name).query().filter(
            'term', tenant_name=schema_name
        )

        logger.info('deleting %i %s objects', s.count(), index._name)
        s.delete()
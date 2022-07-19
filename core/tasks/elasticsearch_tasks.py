from celery.utils.log import get_task_logger
from elasticsearch import ConnectionError as ElasticsearchConnectionError

from core.lib import get_model_by_subtype
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import schema_context
from elasticsearch_dsl import Search

from core.models import Group, Entity
from core.utils.elasticsearch import delete_document_if_found
from core.utils.entity import load_entity_by_id
from tenants.models import Client
from user.models import User
from backend2 import celery_app as app

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
def elasticsearch_recreate_indices(index_name=None):
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


@app.task(ignore_result=True)
def elasticsearch_rebuild_all(index_name=None):
    '''
    Delete indexes, creates indexes and populate tenants

    No option passed then all indices are rebuild
    Options: ['news', 'file', 'question' 'wiki', 'discussion', 'page', 'event', 'blog', 'user', 'group']

    '''
    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_rebuild_for_tenant.delay(client.schema_name, index_name)


@app.task(ignore_result=True)
def elasticsearch_rebuild_for_tenant(schema_name, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild_for_tenant \'%s\' \'%s\'', index_name, schema_name)

        elasticsearch_delete_data_for_tenant(schema_name, index_name)
        elasticsearch_index_data_for_tenant(schema_name, index_name)


@app.task(ignore_result=True)
def elasticsearch_index_data_for_all(index_name=None):
    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_index_data_for_tenant.delay(client.schema_name, index_name)


@app.task(ignore_result=True)
def elasticsearch_index_data_for_tenant(schema_name, index_name=None):
    logger.info('elasticsearch_index_data_for_tenant \'%s\' \'%s\'', index_name, schema_name)
    with schema_context(schema_name):
        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()

        for doc in registry.get_documents(models):
            logger.info("indexing %i '%s' objects",
                        doc().get_queryset().count(),
                        doc.django.model.__name__)
            qs = doc().get_indexing_queryset()

            if doc.django.model.__name__ == 'FileFolder':
                doc().update(qs, parallel=False, chunk_size=10)
            else:
                doc().update(qs, parallel=False, chunk_size=500)


@app.task(ignore_result=True)
def elasticsearch_delete_data_for_tenant(schema_name, index_name=None):
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
        # pylint: disable=protected-access
        s = Search(index=index._name).query().filter(
            'term', tenant_name=schema_name
        )

        logger.info('deleting %i %s objects', s.count(), index._name)
        s.delete()


@app.task(autoretry_for=(ElasticsearchConnectionError,), retry_backoff=10, max_retries=10)
def elasticsearch_index_document(schema_name, document_guid, document_classname):
    with schema_context(schema_name):
        try:
            instance = load_entity_by_id(document_guid, [Group, Entity, User], fail_if_not_found=False)
            if instance:
                registry.update(instance)
                registry.update_related(instance)
            else:
                delete_document_if_found(document_guid)
            return f"{schema_name}.{document_classname}.{document_guid}"
        except ElasticsearchConnectionError as known_error:
            # Fall through for known errors.
            raise known_error
        except Exception as e:
            logger.error(f"elasticsearch_document_index_error: %(error_class)s msg=%(error_message)s schema=%(schema_name)s document=%(document_id)s" % {
                'error_class': e.__class__.__name__,
                'error_message': str(e),
                'schema_name': schema_name,
                'document_id': f"{document_classname}.{document_guid}",
            })

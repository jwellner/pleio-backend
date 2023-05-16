from time import sleep
from traceback import format_exc

from celery import chain
from celery.utils.log import get_task_logger
from elasticsearch import (
    ConnectionError as ElasticsearchConnectionError
)
from core.lib import get_model_by_subtype
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import schema_context
from elasticsearch_dsl import Search, connections

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
        models = _all_models()

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
            logger.error('index %s already exists', index._name)


@app.task(ignore_result=True)
def elasticsearch_rebuild_all(index_name=None):
    '''
    Delete indexes, creates indexes and populate tenants.
    Sites in random order, indexes in sequential order.

    No option passed then all indices are rebuild
    Options: ['news', 'file', 'question' 'wiki', 'discussion', 'page', 'event', 'blog', 'user', 'group']
    '''

    elasticsearch_recreate_indices(index_name)

    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_index_data_for_tenant.delay(client.schema_name, index_name)


@app.task
def elasticsearch_rebuild_all_per_index():
    """
    Delete indexes, create indexes and populate tenants.

    Indexes in parallel, sites in serial.
    """

    signatures = []
    for index in all_indexes():
        # pylint: disable=protected-access
        signatures.append(elasticsearch_rebuild_all_at_index.si(index._name))
    chain(*signatures).apply_async()


@app.task
def elasticsearch_rebuild_all_at_index(index_name):
    elasticsearch_recreate_indices(index_name)

    signatures = []
    for client in Client.objects.exclude(schema_name='public'):
        args = (client.schema_name, index_name)
        signatures.append(elasticsearch_index_data_for_tenant.si(*args))
    chain(*signatures).apply_async()


@app.task(ignore_result=True)
def elasticsearch_rebuild_for_tenant(schema_name, index_name=None):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild index for tenant
    '''
    with schema_context(schema_name):
        if not index_name:
            logger.info('elasticsearch_rebuild_for_tenant \'%s\'', schema_name)
            elasticsearch_delete_data_for_tenant(schema_name, index_name)
            elasticsearch_index_data_for_tenant(schema_name, index_name)
        else:
            for name in index_name.split(','):
                logger.info('elasticsearch_rebuild_for_tenant \'%s\' \'%s\'', name, schema_name)
                elasticsearch_delete_data_for_tenant(schema_name, name)
                elasticsearch_index_data_for_tenant(schema_name, name)


@app.task(ignore_result=True)
def elasticsearch_index_data_for_all(index_name=None):
    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_index_data_for_tenant.delay(client.schema_name, index_name)


@app.task(ignore_result=True)
def elasticsearch_index_data_for_tenant(schema_name, index_name=None):
    logger.info('elasticsearch_index_data_for_tenant \'%s\' \'%s\'', index_name, schema_name)
    with schema_context(schema_name):
        try:
            if index_name:
                models = [get_model_by_subtype(index_name)]
            else:
                models = _all_models()

            for doc in registry.get_documents(models):
                logger.info("indexing %i '%s' objects",
                            doc().get_queryset().count(),
                            doc.django.model.__name__)
                qs = doc().get_indexing_queryset()

                try:
                    if doc.django.model.__name__ == 'FileFolder':
                        doc().update(qs, parallel=False, chunk_size=10)
                    else:
                        doc().update(qs, parallel=False, chunk_size=500)
                except Exception as e:
                    # pylint: disable=logging-not-lazy
                    logger.error("exception at elasticsearch_index_data_for_tenant %s %s: %s" % (
                        schema_name, e.__class__, e))
                    logger.error(format_exc())

        except Exception as e:
            # pylint: disable=logging-not-lazy
            logger.error("exception at elasticsearch_index_data_for_tenant %s %s: %s" % (
                schema_name, e.__class__, e))
            logger.error(format_exc())


@app.task(ignore_result=True)
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
        models = _all_models()

    for index in registry.get_indices(models):
        es_client = connections.get_connection()
        es_client.delete_by_query(
            index=index._name,
            body=Search(index=index._name).filter("term", tenant_name=schema_name).to_dict(),
            conflicts="proceed",
            search_timeout="120s",
            refresh=True
        )


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
            logger.error(
                "Elasticsearch error executing index document task@%s: %s/%s %s/%s",
                schema_name,
                e.__class__.__qualname__,
                e,
                document_classname,
                document_guid
            )


def _all_models():
    def model_weight(model):
        name = model._meta.object_name
        if name == 'Group':
            return 0
        if name == 'User':
            return 1
        if name == 'FileFolder':
            return 100
        return 10

    return sorted(registry.get_models(), key=model_weight)


def all_indexes():
    def index_weight(index):
        # pylint: disable=protected-access
        name = index._name
        if name == 'group':
            return 0
        if name == 'user':
            return 1
        if name == 'file':
            return 100
        return 10

    return sorted(registry.get_indices(), key=index_weight)

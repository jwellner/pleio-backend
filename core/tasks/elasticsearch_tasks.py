from celery import shared_task
from celery.utils.log import get_task_logger
from core.lib import get_model_by_subtype
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import schema_context
from elasticsearch_dsl import Search
from file.models import FileFolder
from tenants.models import Client

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
            logger.info('created index %s')
        except Exception:
            logger.info('index %s already exists')


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
def elasticsearch_repopulate_index_for_tenant(self, schema_name, index_name):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Rebuild index for tenant
    '''
    with schema_context(schema_name):
        if index_name:
            models = [get_model_by_subtype(index_name)]
        else:
            models = registry.get_models()


        for index in registry.get_indices(models):
            logger.info('elasticsearch_repopulate_index_for_tenant \'%s\' \'%s\'', index_name, schema_name)

            # delete all objects for tenant before updating
            s = Search(index=index._name).query().filter(
                'term', tenant_name=schema_name
            )

            logger.info('deleting %i objects', s.count())
            s.delete()

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

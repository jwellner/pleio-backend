import time
from django.conf import settings
from django.test.runner import DiscoverRunner, ParallelTestSuite
from django.db import connections

_worker_id = 0

def _init_worker(counter):
    """
    Switch to databases dedicated to this worker.

    This helper lives at module-level because of the multiprocessing module's
    requirements.
    """

    global _worker_id

    with counter.get_lock():
        counter.value += 1
        _worker_id = counter.value

    for alias in connections:
        connection = connections[alias]
        settings_dict = connection.creation.get_test_db_clone_settings(str(_worker_id))
        # connection.settings_dict must be updated in place for changes to be
        # reflected in django.db.connections. If the following line assigned
        # connection.settings_dict = settings_dict, new threads would connect
        # to the default database instead of the appropriate clone.
        connection.settings_dict.update(settings_dict)
        connection.close()

    ### Everything above this is from the Django version of this function ###

    from elasticsearch_dsl.connections import connections as es_connections
    # each worker needs its own connection to elasticsearch, the ElasticsearchClient uses
    # global connection objects that do not play nice otherwise

    es_connections.create_connection(hosts=[settings.ELASTICSEARCH_DSL["default"]["hosts"]], alias='default', maxsize=15)
    print('Elasticsearch connection created for worker %s' % _worker_id)

class ElasticsearchParallelTestSuite(ParallelTestSuite):
    init_worker = _init_worker

class PleioTestRunner(DiscoverRunner):
    parallel_test_suite = ElasticsearchParallelTestSuite
    # This method sets up the test environment before the tests are run.
    def setup_test_environment(self, *args, **kwargs):
        super().setup_test_environment(*args, **kwargs)

        # disable elasticsearch autosync, we populate the index manually
        settings.ELASTICSEARCH_DSL_AUTOSYNC = False

        # make sure tests start with clean index
        from core.tasks.elasticsearch_tasks import elasticsearch_recreate_indices
        from core.tests.helpers import suppress_stdout
        with suppress_stdout():
            elasticsearch_recreate_indices()
            time.sleep(0.1)

        print('Elasticsearch indices recreated')

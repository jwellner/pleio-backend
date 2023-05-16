import time
from django.test.runner import DiscoverRunner


class PleioTestRunner(DiscoverRunner):
    # This method sets up the test environment before the tests are run.
    def setup_test_environment(self, *args, **kwargs):
        super().setup_test_environment(*args, **kwargs)
        # make sure tests start with clean index
        from core.tasks.elasticsearch_tasks import elasticsearch_recreate_indices
        from core.tests.helpers import suppress_stdout
        with suppress_stdout():
            elasticsearch_recreate_indices()
            time.sleep(0.1)

        print('Elasticsearch indices recreated')

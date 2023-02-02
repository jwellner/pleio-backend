from core.exceptions import IgnoreIndexError


def get_entity_filters():
    from .models import ExternalContentSource
    for source in ExternalContentSource.objects.all():
        yield {
            "key": source.guid,
            "value": source.name,
        }


def get_search_filters():
    from .models import ExternalContentSource
    for source in ExternalContentSource.objects.all():
        yield {
            "key": source.guid,
            "value": source.name,
            "plural": source.plural_name,
        }


def get_hourly_cron_jobs():
    from external_content.tasks import fetch_external_content
    yield fetch_external_content


def test_elasticsearch_index(index_name):
    """
    # TODO: implement this test
    """
    if index_name != 'externalcontent':
        raise IgnoreIndexError()

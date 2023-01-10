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

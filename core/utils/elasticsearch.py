from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q


def delete_document_if_found(uuid):
    for index in registry.get_indices():
        result = index.search().filter(Q("term", id=uuid)).execute()
        if result:
            result[0].delete()

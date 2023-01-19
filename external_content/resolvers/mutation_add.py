from core.resolvers import shared
from external_content.api_handlers.datahub import ApiHandler
from external_content.models import ExternalContentSource
from external_content.resolvers.query import resolve_query_external_content_sources


def add_datahub_external_content_source(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    shared.assert_authenticated(user)
    shared.assert_administrator(user)

    source = ExternalContentSource.objects.create(
        handler_id=ApiHandler.ID,
        name=input['name'],
        plural_name=input['pluralName'],
        settings={
            "apiUrl": input['apiUrl'],
            "frontendUrl": input['frontendUrl'],
            "batchSize": input['batchSize']
        }
    )
    return resolve_query_external_content_sources(_, info, source.handler_id)

from django.utils import timezone
from graphql import GraphQLError

from core import constances
from core.resolvers import shared
from external_content.api_handlers.datahub import ApiHandler
from external_content.models import ExternalContentSource
from external_content.resolvers.query import resolve_query_external_content_sources


def edit_datahub_external_content_source(_, info, input):
    # pylint: disable=redefined-builtin
    try:
        user = info.context["request"].user
        shared.assert_authenticated(user)
        shared.assert_administrator(user)

        source = ExternalContentSource.objects.get(pk=input['key'])
        source.handler_id = ApiHandler.ID

        if 'name' in input:
            source.name = input['name']
        if 'pluralName' in input:
            source.plural_name = input['pluralName']

        if 'apiUrl' in input:
            source.settings['apiUrl'] = input['apiUrl']
        if 'frontendUrl' in input:
            source.settings['frontendUrl'] = input['frontendUrl']
        if 'batchSize' in input:
            source.settings['batchSize'] = input['batchSize']

        source.updated_at = timezone.now()
        source.save()

        return resolve_query_external_content_sources(_, info, source.handler_id)
    except ExternalContentSource.DoesNotExist:
        raise GraphQLError(constances.COULD_NOT_FIND)

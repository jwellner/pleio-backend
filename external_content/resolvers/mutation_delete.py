from graphql import GraphQLError

from core import constances
from core.resolvers import shared
from external_content.models import ExternalContentSource, ExternalContent
from external_content.resolvers.query import resolve_query_external_content_sources


def resolve_delete_external_content_source(_, info, key):
    try:
        user = info.context["request"].user
        shared.assert_authenticated(user)
        shared.assert_administrator(user)

        source = ExternalContentSource.objects.get(pk=key)
        handler_id = source.handler_id

        for entity in ExternalContent.objects.filter(source=source):
            entity.delete()

        source.delete()

        return resolve_query_external_content_sources(_, info, handler_id)
    except ExternalContentSource.DoesNotExist:
        raise GraphQLError(constances.COULD_NOT_FIND)

from ariadne import ObjectType

from core.resolvers import shared
from external_content.models import ExternalContentSource

query = ObjectType("Query")


@query.field('externalContentSources')
def resolve_query_external_content_sources(_, info, handlerId):
    user = info.context["request"].user
    shared.assert_authenticated(user)
    shared.assert_administrator(user)

    return {
        'edges': ExternalContentSource.objects.filter(handler_id=handlerId)
    }

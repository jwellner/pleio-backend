import graphene
from core.lists import EntityList
from core.entities import Entity

class Query(object):
    files = graphene.Field(
        EntityList,
        filter=graphene.String(),
        orderBy=graphene.String(),
        direction=graphene.String(),
        containerGuid=graphene.Int(),
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    breadcrumb = graphene.Field(
        Entity,
        guid = graphene.ID()
    )

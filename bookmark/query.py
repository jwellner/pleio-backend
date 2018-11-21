import graphene
from core.lists import EntityList

class Query(object):
    bookmarks = graphene.Field(
        EntityList,
        subtype=graphene.String(),
        tags=graphene.List(graphene.String),
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    def resolve_bookmarks(self, info, subtype, tags, offset=0, limit=20):
        return EntityList(
            total=0,
            edges=[]
        )

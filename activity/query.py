import graphene
from .lists import ActivityList

class Query(object):
    activities = graphene.Field(
        ActivityList,
        containerGuid=graphene.Int(),
        tags=graphene.List(graphene.String),
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    def resolve_events(self, info, containerGuid, tags, offset=0, limit=20):
        return ActivityList(
            total=0,
            edges=[]
        )

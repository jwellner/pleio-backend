import graphene


class EventList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('event.entities.Event')

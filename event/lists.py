import graphene


class EventList(graphene.ObjectType):
    total = graphene.Int(required=True)
    can_write = graphene.Boolean(required=True)
    edges = graphene.List('event.entities.Event')

import graphene


class EventList(graphene.ObjectType):
    total = graphene.Int(required=True)
    can_write = graphene.Boolean(required=True)
    edges = graphene.List('event.entities.Event')

class AttendeesList(graphene.ObjectType):
    total = graphene.Int(required=True)
    total_maybe = graphene.Int(required=True)
    total_rejected = graphene.Int(required=True)
    edges = graphene.List('core.entities.User')

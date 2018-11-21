import graphene

class ActivityList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('activity.entities.Activity')

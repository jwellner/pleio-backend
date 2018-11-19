import graphene


class GroupList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.entities.Group')


class MembersList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.entities.GroupMembership')


class EntityList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.entities.Entity')

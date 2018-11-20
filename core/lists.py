import graphene


class GroupList(graphene.ObjectType):
    total = graphene.Int(required=True)
    can_write = graphene.Boolean(required=True)
    edges = graphene.List('core.entities.Group')

class MembersList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.entities.User')

class EntityList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.entities.Entity')

class InviteList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Invite')

class MembershipRequestList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Member')

class SubgroupList(graphene.ObjectType):
    totel = graphene.Int(required=True)
    edges = graphene.List('core.entities.Subgroup')

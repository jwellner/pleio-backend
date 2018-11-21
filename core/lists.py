import graphene

class GroupList(graphene.ObjectType):
    total = graphene.Int(required=True)
    can_write = graphene.Boolean(required=True)
    edges = graphene.List('core.entities.Group')

class MembersList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Member')

class EntityList(graphene.ObjectType):
    total = graphene.Int(required=True)
    can_write = graphene.Boolean(required=True)
    edges = graphene.List('core.entities.Entity')

class InviteList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Invite')

class MembershipRequestList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Member')

class SubgroupList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.Subgroup')

class SearchList(graphene.ObjectType):
    total = graphene.Int(required=True)
    totals = graphene.List('core.entities.SearchTotal')
    edges = graphene.List('core.entities.Entity')

class UserList(graphene.ObjectType):
    total = graphene.Int(required=True)
    edges = graphene.List('core.entities.User')

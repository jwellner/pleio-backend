import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User, Group, GroupMembership
from .lists import PaginatedMembersList

class Node(graphene.Interface):
    id = graphene.ID()

class UserNode(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name', 'picture']
        interfaces = (Node, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

class GroupNode(DjangoObjectType):
    class Meta:
        model = Group
        interfaces = (Node, )

    members = graphene.Field(PaginatedMembersList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

    def resolve_members(self, info, offset=0, limit=20):
        return PaginatedMembersList(
            totalCount=self.members.count(),
            edges=self.members.all()[offset:(offset+limit)]
        )

class GroupMembershipNode(DjangoObjectType):
    class Meta:
        model = GroupMembership
        interfaces = (Node, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

class ViewerNode(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserNode)

import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User, Group, GroupMembership, Comment
from .lists import PaginatedMembersList

class ViewerNode(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field('core.nodes.UserNode')

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
        only_fields = ['id', 'name', 'description', 'created_at', 'updated_at' ,'is_open', 'is_2FA_required', 'tags', 'members', 'is_member']
        interfaces = (Node, )

    members = graphene.Field(PaginatedMembersList, offset=graphene.Int(), limit=graphene.Int())
    is_member = graphene.Boolean(required=True)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

    def resolve_members(self, info, offset=0, limit=20):
        return PaginatedMembersList(
            totalCount=self.members.count(),
            edges=self.members.all()[offset:(offset+limit)]
        )

    def resolve_is_member(self, info):
        return self.is_member(info.context.user)

class GroupMembershipNode(DjangoObjectType):
    class Meta:
        model = GroupMembership
        interfaces = (Node, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

class CommentNode(DjangoObjectType):
    id = graphene.ID()

    class Meta:
        only_fields = ['id', 'owner', 'description', 'created_at', 'updated_at']
        model = Comment

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()
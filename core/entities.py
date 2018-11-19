import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User as UserModel, Group as GroupModel, GroupMembership as GroupMembershipModel, Comment as CommentModel

from .lists import MembersList


class Viewer(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field('core.entities.User')


class Entity(graphene.Interface):
    id = graphene.ID()


class User(DjangoObjectType):
    class Meta:
        model = UserModel
        only_fields = ['id', 'name', 'picture']
        interfaces = (Entity, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()


class Group(DjangoObjectType):
    class Meta:
        model = GroupModel
        only_fields = [
            'id',
            'name',
            'description',
            'created_at',
            'updated_at',
            'is_open',
            'is_2fa_required',
            'tags',
            'members',
            'is_member'
            ]
        interfaces = (Entity, )

    members = graphene.Field(
        MembersList, offset=graphene.Int(), limit=graphene.Int()
        )
    is_member = graphene.Boolean(required=True)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()

    def resolve_members(self, info, offset=0, limit=20):
        return MembersList(
            totalCount=self.members.count(),
            edges=self.members.all()[offset:(offset+limit)]
        )

    def resolve_is_member(self, info):
        return self.is_member(info.context.user)


class GroupMembership(DjangoObjectType):
    class Meta:
        model = GroupMembershipModel
        interfaces = (Entity, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()


class Comment(DjangoObjectType):
    id = graphene.ID()

    class Meta:
        only_fields = [
            'id',
            'owner',
            'description',
            'created_at',
            'updated_at'
            ]
        model = CommentModel

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()

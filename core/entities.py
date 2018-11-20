import graphene, logging
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User as UserModel, Group as GroupModel, GroupMembership as GroupMembershipModel, Comment as CommentModel
from .lists import MembersList, InviteList, MembershipRequestList, SubgroupList

logger = logging.getLogger(__name__)

MEMBERSHIP = graphene.Enum('Membership', [
    ('not_joined', 'not_joined'),
    ('requested', 'requested'),
    ('invited', 'invited'),
    ('joined', 'joined')
])

PLUGIN = graphene.Enum('Plugins', [
    ('events', 'events'),
    ('blog', 'blog'),
    ('discussion', 'discussion'),
    ('questions', 'questions'),
    ('files', 'files'),
    ('wiki', 'wiki'),
    ('tasks', 'tasks')
])

ROLE = graphene.Enum('Role', [
    ('owner', 'owner'),
    ('admin', 'admin'),
    ('member', 'member'),
    ('removed', 'removed')
])

class Featured(graphene.ObjectType):
    video = graphene.String()
    image = graphene.String()
    positionY = graphene.Int()

class Viewer(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field('core.entities.User')

class Entity(graphene.Interface):
    guid = graphene.ID()

class User(DjangoObjectType):
    class Meta:
        model = UserModel
        only_fields = ['id', 'name', 'picture']
        interfaces = (Entity, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()

class Member(DjangoObjectType):
    class Meta:
        model = GroupMembershipModel
        only_fields = ['user']

    role = ROLE()
    email = graphene.String()

    def resolve_role(self, info):
        return self.type

    def resolve_email(self, info):
        return self.user.email

class Group(DjangoObjectType):
    class Meta:
        model = GroupModel
        only_fields = [
            'name',
            'description',
            'richDescription',
            'excerp',
            'introduction',
            'icon',
            'url',
            'is_featured',
            'is_closed',
            'auto_notification',
            'welcome_message'
        ]
        interfaces = (Entity, )

    guid = graphene.ID(required=True)

    featured = graphene.Field(Featured)
    is_member = graphene.Boolean(required=True)
    can_edit = graphene.Boolean()
    can_change_ownership = graphene.Boolean()
    membership = MEMBERSHIP()
    access_ids = graphene.List(graphene.Int)
    default_access_id = graphene.Int()
    gets_notifications = graphene.Boolean()
    tags = graphene.List(graphene.String)
    members = graphene.Field(
        MembersList, q=graphene.String(), offset=graphene.Int(), limit=graphene.Int(), in_subgroup_id=graphene.Int(), not_in_subgroup_id=graphene.Int()
    )
    invite = graphene.Field(
        InviteList, q=graphene.String(), offset=graphene.Int(), limit=graphene.Int()
    )
    invited = graphene.Field(
        InviteList, q=graphene.String(), offset=graphene.Int(), limit=graphene.Int()
    )
    membership_requests = graphene.Field(
        MembershipRequestList
    )
    plugins = graphene.List(PLUGIN)
    subgroups = graphene.Field(
        SubgroupList
    )

    def resolve_featured(self, info):
        return(Featured(
            video=self.featured_video,
            image=self.featured_image,
            positionY=self.featured_position_y
        ))

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()

    def resolve_members(self, info, offset=0, limit=20):
        return MembersList(
            total=self.members.count(),
            edges=self.members.all()[offset:(offset+limit)]
        )

    def resolve_is_member(self, info):
        return self.is_member(info.context.user)


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

class Invite(graphene.ObjectType):
    id = graphene.ID()
    time_created = graphene.String()
    invited = graphene.NonNull(graphene.Boolean)
    user = User
    email = graphene.String()

class Subgroup(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    members = graphene.List(User)

import graphene, logging
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User as UserModel, Group as GroupModel, GroupMembership as GroupMembershipModel, Comment as CommentModel
from .lists import MembersList, InviteList, MembershipRequestList, SubgroupList
from .enums import MEMBERSHIP, PLUGIN, ROLE

logger = logging.getLogger(__name__)

Membership = graphene.Enum.from_enum(MEMBERSHIP)
Plugin = graphene.Enum.from_enum(PLUGIN)
Role = graphene.Enum.from_enum(ROLE)

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
        only_fields = ['name', 'picture']
        interfaces = (Entity, )

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label, self._meta.object_name, self.id
            ).lower()

class Member(DjangoObjectType):
    class Meta:
        model = GroupMembershipModel
        only_fields = ['user']

    role = Role()
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
    membership = Membership()
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
    plugins = graphene.List(Plugin)
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

class SearchTotal(graphene.ObjectType):
    subtype = graphene.String(required=True)
    total = graphene.Int(required=True)

class MenuItem(graphene.ObjectType):
    title = graphene.String(required=True)
    link = graphene.String()
    children = graphene.List('core.entities.MenuItem')

class ProfileItem(graphene.ObjectType):
    key = graphene.String(required=True)
    name = graphene.String(required=True)
    value = graphene.String()
    accessId = graphene.Int()

class DirectLink(graphene.ObjectType):
    title = graphene.String(required=True)
    link = graphene.String(required=True)

class AccessId(graphene.ObjectType):
    id = graphene.String(required=True)
    description = graphene.String(required=True)

class StyleType(graphene.ObjectType):
    colorPrimary = graphene.String()
    colorSecondary = graphene.String()
    colorTertiary = graphene.String()
    colorQuaternary = graphene.String()

class Filter(graphene.ObjectType):
    name = graphene.String(required=True)
    values = graphene.List(graphene.String)

class PredifinedTagType(graphene.ObjectType):
    tag = graphene.String()

class Site(graphene.ObjectType):
    guid = graphene.ID(required=True)
    name = graphene.String(required=True)
    theme = graphene.String(required=True)
    menu = graphene.List('core.entities.MenuItem')
    profile = graphene.List('core.entities.ProfileItem')
    footer = graphene.List('core.entities.MenuItem')
    directLinks = graphene.List('core.entities.DirectLink')
    accessIds = graphene.List('core.entities.AccessId')
    defaultAccessId = graphene.Int(required=True)
    logo = graphene.String()
    icon = graphene.String()
    showIcon = graphene.Boolean(required=True)
    initiatorLink = graphene.String()
    startPage = graphene.String()
    showLeader = graphene.Boolean(required=True)
    showLeaderButtons = graphene.Boolean(required=True)
    subtitle = graphene.String()
    leaderImage = graphene.String()
    showInitiative = graphene.Boolean(required=True)
    initiativeImage = graphene.String()
    style = graphene.Field('core.entities.StyleType')
    filters = graphene.List('core.entities.Filter')
    predefinedTags = graphene.List('core.entities.PredifinedTagType')
    usersOnline = graphene.Boolean(required=True)

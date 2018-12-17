import graphene, logging
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType
from .models import User as UserModel, Group as GroupModel, GroupMembership as GroupMembershipModel, Comment as CommentModel
from .lists import MembersList, InviteList, MembershipRequestList, SubgroupList
from .enums import MEMBERSHIP, PLUGIN, ROLE, EMAIL_FREQUENCY, OBJECT_TYPE

logger = logging.getLogger(__name__)

Membership = graphene.Enum.from_enum(MEMBERSHIP)
Plugin = graphene.Enum.from_enum(PLUGIN)
Role = graphene.Enum.from_enum(ROLE)
EmailFrequency = graphene.Enum.from_enum(EMAIL_FREQUENCY)
ObjectType = graphene.Enum.from_enum(OBJECT_TYPE)

class Featured(graphene.ObjectType):
    video = graphene.String()
    image = graphene.String()
    positionY = graphene.Int()

class Viewer(graphene.ObjectType):
    guid = graphene.String(required=True)
    logged_in = graphene.Boolean(required=True)
    is_sub_editor = graphene.Boolean(required=True)
    is_admin = graphene.Boolean(required=True)
    tags = graphene.List(graphene.String)
    user = graphene.Field('core.entities.User')
    can_write_to_container = graphene.Field(
        graphene.Boolean,
        containerGuid=graphene.Int(),
        _type=ObjectType(name='type'),
        subtype=graphene.String(),
        required=True
    )

class Entity(graphene.Interface):
    guid = graphene.ID()
    status = graphene.Int()

class User(DjangoObjectType):
    class Meta:
        model = UserModel
        only_fields = ['name']
        interfaces = (Entity, )

    username = graphene.String()
    icon = graphene.String()
    email = graphene.String()
    emailNotifications = graphene.Boolean()
    getsNewsletter = graphene.Boolean()
    emailOverview = EmailFrequency()
    profile = graphene.List('core.entities.ProfileItem')
    stats = graphene.List('core.entities.StatsItem')
    tags = graphene.List(graphene.String)
    url = graphene.String()
    can_edit = graphene.Boolean()

    def resolve_email(self, info):
        return self.email

    def resolve_username(self, info):
        return self.name

    def resolve_guid(self, info):
        return self.guid()

    def resolve_icon(self, info):
        return self.picture

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
            'excerpt',
            'introduction',
            'icon',
            'url',
            'is_featured',
            'is_closed',
            'auto_notification',
            'welcome_message'
        ]
        interfaces = (Entity, )

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

    class Meta:
        only_fields = [
            'owner',
            'description',
            ]
        model = CommentModel
        interfaces = (Entity, )

    subtype = graphene.String()
    title = graphene.String()
    description = graphene.String()
    rich_description = graphene.String()
    excerpt = graphene.String()
    url = graphene.String()
    tags = graphene.List(graphene.String)
    time_created = graphene.String()
    time_updated = graphene.String()
    can_edit = graphene.Boolean()
    can_vote = graphene.Boolean()
    access_id = graphene.Int()
    write_access_id = graphene.Int()
    has_voted = graphene.Boolean()
    votes = graphene.Int()
    can_choose_best_answer = graphene.Boolean()
    is_best_answer = graphene.Boolean()
    owner = graphene.Field('core.entities.User')

    def resolve_guid(self, info):
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
    font = graphene.String()
    color_primary = graphene.String()
    color_secondary = graphene.String()
    color_tertiary = graphene.String()
    color_quaternary = graphene.String()

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
    direct_links = graphene.List('core.entities.DirectLink')
    access_ids = graphene.List('core.entities.AccessId')
    default_access_id = graphene.Int(required=True)
    logo = graphene.String()
    icon = graphene.String()
    show_icon = graphene.Boolean(required=True)
    initiator_link = graphene.String()
    start_page = graphene.String()
    show_leader = graphene.Boolean(required=True)
    show_leader_buttons = graphene.Boolean(required=True)
    subtitle = graphene.String()
    leader_image = graphene.String()
    show_initiative = graphene.Boolean(required=True)
    initiative_image = graphene.String()
    style = graphene.Field('core.entities.StyleType')
    filters = graphene.List('core.entities.Filter')
    predefined_tags = graphene.List('core.entities.PredifinedTagType')
    users_online = graphene.Boolean(required=True)

class StatsItem(graphene.ObjectType):
    key = graphene.String(required=True)
    name = graphene.String(required=True)
    value = graphene.String()

import graphene
from graphene_django.types import DjangoObjectType
from core.entities import Entity
from .enums import ACTIVITY_TYPES
from .models import StatusUpdate as StatusUpdateModel

ActivityType = graphene.Enum.from_enum(ACTIVITY_TYPES)

class Activity(graphene.ObjectType):
    guid = graphene.ID()
    type = ActivityType()
    entity = graphene.Field('core.entities.Entity')

class StatusUpdate(DjangoObjectType):
    class Meta:
        model = StatusUpdateModel
        interfaces = (Entity, )

    subtype = graphene.String()
    title = graphene.String()
    description = graphene.String()
    rich_description = graphene.String()
    in_group = graphene.Boolean()
    group = graphene.Field('core.entities.Group')
    excerpt = graphene.String()
    url = graphene.String()
    tags = graphene.List(graphene.String)
    time_created = graphene.String()
    time_updated = graphene.String()
    can_edit = graphene.Boolean()
    can_comment = graphene.Boolean()
    can_vote = graphene.Boolean()
    access_id = graphene.Int()
    write_access_id = graphene.Int()
    is_bookmarked = graphene.Boolean()
    is_following = graphene.Boolean()
    can_bookmark = graphene.Boolean()
    has_voted = graphene.Boolean()
    votes = graphene.Int()
    views = graphene.Int()
    owner = graphene.Field('core.entities.User')
    comments = graphene.List('core.entities.Comment')
    comment_count = graphene.Int()

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

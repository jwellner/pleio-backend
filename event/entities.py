import graphene
from graphene_django.types import DjangoObjectType
from graphene import relay
from core.entities import Entity
from .models import Event as EventModel
from .lists import AttendeesList

class Event(DjangoObjectType):
    class Meta:
        model = EventModel
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
    start_date = graphene.String()
    end_date = graphene.String()
    location = graphene.String()
    source = graphene.String()
    max_attendees = graphene.String()
    rsvp = graphene.Boolean()
    is_featured = graphene.Boolean()
    is_highlighted = graphene.Boolean()
    is_recommended = graphene.Boolean()
    featured = graphene.Field('core.entities.Featured')
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
    is_attending =graphene.Boolean()
    attendees = graphene.Field(
        AttendeesList,
        offset=graphene.Int(),
        limit=graphene.Int(),
        state=graphene.String()
    )
    comments = graphene.List('core.entities.Comment')
    comment_count = graphene.Int()

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()


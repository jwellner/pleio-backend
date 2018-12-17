import graphene
from graphene_django.types import DjangoObjectType
from core.entities import Entity
from .models import Poll as PollModel

class Poll(DjangoObjectType):
    class Meta:
        model = PollModel
        interfaces = (Entity, )

    can_edit = graphene.Boolean(required=True)
    title = graphene.String()
    url = graphene.String()
    time_created = graphene.String()
    time_updated = graphene.String()
    access_id = graphene.Int()
    choices = graphene.List('poll.entities.PollChoice')
    has_voted = graphene.Boolean()

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

    def resolve_can_edit(self, info):
        return self.can_write(info.context.user)

class PollChoice(graphene.ObjectType):
    guid = graphene.ID()
    text = graphene.String()
    votes = graphene.Int()

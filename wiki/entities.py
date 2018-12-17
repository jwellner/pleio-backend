import graphene
from graphene_django.types import DjangoObjectType
from core.entities import Entity
from .models import Wiki as WikiModel


class Wiki(DjangoObjectType):
    class Meta:
        model = WikiModel
        interfaces = (Entity, )

    can_edit = graphene.Boolean(required=True)
    title = graphene.String()
    description = graphene.String()
    has_children = graphene.Boolean()
    children = graphene.List('wiki.entities.Wiki')
    rich_description = graphene.String()
    excerpt = graphene.String()
    url = graphene.String()
    time_created = graphene.String()
    time_updated = graphene.String()
    access_id = graphene.Int()
    is_bookmarked = graphene.Boolean()
    can_bookmark = graphene.Boolean()
    tags = graphene.List(graphene.String)
    group = graphene.Field('core.entities.Group')

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

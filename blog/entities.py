import graphene
from graphene_django.types import DjangoObjectType
from core.entities import Entity, Comment, Group
from .models import Blog as BlogModel

class Blog(DjangoObjectType):
    class Meta:
        model = BlogModel
        interfaces = (Entity, )

    can_write = graphene.Boolean(required=True)
    comments = graphene.List(Comment)
    subtype = graphene.String()
    title = graphene.String()
    url = graphene.String()
    description = graphene.String()
    richDescription = graphene.String()
    in_group = graphene.Boolean()
    group = graphene.Field('core.entities.Group')
    excerpt = graphene.String()
    tags = graphene.List(graphene.String)
    time_created = graphene.String()
    time_updated = graphene.String()
    is_featured = graphene.Boolean()
    is_highlighted = graphene.Boolean()
    is_recommended = graphene.Boolean()
    featured = graphene.Field('core.entities.Featured')
    can_edit = graphene.Boolean()
    can_vote = graphene.Boolean()
    access_id = graphene.Int()
    write_access_id = graphene.Int()
    is_bookmarked = graphene.Boolean()
    is_following = graphene.Boolean()
    can_bookmark = graphene.Boolean()
    has_voted = graphene.Boolean()
    votes = graphene.Int()
    owner = graphene.Field('core.entities.User')
    comments = graphene.List('core.entities.Comment')
    comment_count = graphene.Int()

    def resolve_guid(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

    def resolve_can_write(self, info):
        return self.can_write(info.context.user)

    def resolve_comments(self, info):
        return self.comments.visible(
            self._meta.app_label.lower(),
            self._meta.object_name.lower(),
            self.id
            )

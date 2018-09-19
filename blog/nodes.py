import graphene
from graphene_django.types import DjangoObjectType
from core.nodes import Node, CommentNode
from core.models import Comment
from .models import Blog

class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        interfaces = (Node, )

    can_write = graphene.Boolean(required=True)
    comments = graphene.List(CommentNode)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()

    def resolve_can_write(self, info):
        return self.can_write(info.context.user)

    def resolve_comments(self, info):
        return self.comments.visible(self._meta.app_label.lower(), self._meta.object_name.lower(), self.id)
import graphene
from .nodes import ViewerNode, GroupNode
from graphene_django.filter import DjangoFilterConnectionField

class Query(object):
    viewer = graphene.Field(ViewerNode)
    groups = DjangoFilterConnectionField(GroupNode)

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user

        return ViewerNode(
            is_authenticated=user.is_authenticated,
            user=(user if user.is_authenticated else None)
        )

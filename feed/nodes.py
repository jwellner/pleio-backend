from graphene_django.types import DjangoObjectType
import graphene
from graphene import relay
from core.lib import get_type, get_id
from core.nodes import Node
from .models import Feed

class FeedNode(DjangoObjectType):
    class Meta:
        model = Feed
        interfaces = (Node, )
        only_fields = ['id']

    node = graphene.Field(Node)

    def resolve_id(self, info):
        return 'feed:{}'.format(self.id)

    def resolve_node(self, info):
        return self.node

class PaginatedFeedList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List(FeedNode)

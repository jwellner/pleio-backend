import graphene
from graphene_django.types import DjangoObjectType
from core.nodes import Node
from .models import Question


class QuestionNode(DjangoObjectType):
    class Meta:
        model = Question
        interfaces = (Node, )

    can_write = graphene.Boolean(required=True)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

    def resolve_can_write(self, info):
        return self.can_write(info.context.user)

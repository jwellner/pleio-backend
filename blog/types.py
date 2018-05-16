from graphene_django.types import DjangoObjectType
from .models import Blog

class BlogType(DjangoObjectType):
    class Meta:
        model = Blog

    def resolve_id(self, info):
        return 'blog:{}'.format(self.id)

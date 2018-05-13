from graphene_django.types import DjangoObjectType
from .models import Blog

class BlogType(DjangoObjectType):
    class Meta:
        model = Blog

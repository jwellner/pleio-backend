import graphene
from .types import ViewerType, GroupType
from .models import Group

class Query(object):
    viewer = graphene.Field(ViewerType)
    groups = graphene.List(GroupType)

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user
        return ViewerType(is_authenticated=user.is_authenticated, user=(user if user.is_authenticated else None))

    def resolve_groups(self, info, **kwargs):
        return Group.objects.all()

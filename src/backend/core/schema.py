import graphene

from .types import GroupType
from backend.core.models import Group

class Query(object):
    all_groups = graphene.List(GroupType)

    def resolve_all_groups(self, info, **kwargs):
        return Group.objects.all()

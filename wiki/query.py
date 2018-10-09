import graphene
from .lists import PaginatedWikiList
from .nodes import WikiNode
from .models import Wiki


class Query(object):
    wikis = graphene.Field(
        PaginatedWikiList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_wikis(self, info, offset=0, limit=20):
        return PaginatedWikiList(
            totalCount=Wiki.objects.visible(info.context.user).count(),
            edges=Wiki.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )

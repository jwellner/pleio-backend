import graphene
from .lists import WikiList
from .models import Wiki as WikiModel


class Query(object):
    wikis = graphene.Field(
        WikiList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_wikis(self, info, offset=0, limit=20):
        return WikiList(
            totalCount=WikiModel.objects.visible(info.context.user).count(),
            edges=WikiModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )

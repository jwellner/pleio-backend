import graphene
from .lists import PaginatedCmsPageList
from .nodes import CmsPageNode
from .models import CmsPage


class Query(object):
    cms_pages = graphene.Field(
        PaginatedCmsPageList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_cms_pages(self, info, offset=0, limit=20):
        return PaginatedCmsPageList(
            totalCount=CmsPage.objects.visible(info.context.user).count(),
            edges=CmsPage.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )

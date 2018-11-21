import graphene
from .lists import CmsPageList
from .models import CmsPage as CmsPageModel


class Query(object):
    """
    Does not exist in old graphQL schema

    cms_pages = graphene.Field(
        CmsPageList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_cms_pages(self, info, offset=0, limit=20):
        return CmsPageList(
            totalCount=CmsPageModel.objects.visible(info.context.user).count(),
            edges=CmsPageModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
    """

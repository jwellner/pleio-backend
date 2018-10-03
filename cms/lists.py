import graphene


class PaginatedCmsPageList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('cms.nodes.CmsPageNode')

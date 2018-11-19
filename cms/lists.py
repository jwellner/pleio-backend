import graphene


class CmsPageList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('cms.entities.CmsPage')

import graphene


class PaginatedBlogList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('blog.nodes.BlogNode')

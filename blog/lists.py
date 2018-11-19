import graphene


class BlogList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('blog.entities.Blog')

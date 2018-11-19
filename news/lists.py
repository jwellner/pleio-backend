import graphene


class NewsList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('news.entities.News')

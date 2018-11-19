import graphene


class WikiList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('wiki.entities.Wiki')

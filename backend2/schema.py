import graphene

from .utils import get_queries_from_apps, get_mutations_from_apps

name = 'Query'
Query = type(
    name,
    get_queries_from_apps() + (graphene.ObjectType,),
    dict()
)

name = 'Mutation'
Mutation = type(
    name,
    get_mutations_from_apps() + (graphene.ObjectType,),
    dict()
)

schema = graphene.Schema(query=Query, mutation=Mutation)

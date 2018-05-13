import graphene

import backend.core.query
import backend.blog.query

import backend.core.mutation
import backend.blog.mutation

class Query(backend.core.query.Query, backend.blog.query.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

class Mutation(backend.core.mutation.Mutation, backend.blog.mutation.Mutation, graphene.ObjectType):
    # This class will inherit from multiple Mutations
    # as we begin to add more apps to our project
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
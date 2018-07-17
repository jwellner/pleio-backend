import graphene

class PaginatedQuestionList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('question.nodes.QuestionNode')

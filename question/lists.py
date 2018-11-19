import graphene


class QuestionList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('question.entities.Question')

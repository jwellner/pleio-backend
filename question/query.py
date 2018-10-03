import graphene
from .lists import PaginatedQuestionList
from .nodes import QuestionNode
from .models import Question


class Query(object):
    questions = graphene.Field(
        PaginatedQuestionList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_questions(self, info, offset=0, limit=20):
        return PaginatedQuestionList(
            totalCount=Question.objects.visible(info.context.user).count(),
            edges=Question.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )

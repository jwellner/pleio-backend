import graphene
from .lists import QuestionList
from .models import Question as QuestionModel


class Query(object):
    """
    Does not exist in old graphQL schema

    questions = graphene.Field(
        QuestionList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_questions(self, info, offset=0, limit=20):
        return QuestionList(
            totalCount=QuestionModel.objects.visible(info.context.user).count(),
            edges=QuestionModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
    """

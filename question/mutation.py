import graphene
import reversion

from core.lib import get_id
from .models import Question
from .nodes import QuestionNode

class QuestionInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)

class CreateQuestion(graphene.Mutation):
    class Arguments:
        input = QuestionInput(required=True)

    ok = graphene.Boolean()
    question = graphene.Field(lambda: QuestionNode)

    def mutate(self, info, title, description):
        try:
            with reversion.create_revision():
                question = Question.objects.create(
                    owner=info.context.user,
                    title=title,
                    description=description
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createQuestion mutation")

            ok = True
        except:
            question = None
            ok = False

        return CreateQuestion(question=question, ok=ok)

class UpdateQuestion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = QuestionInput(required=True)

    ok = graphene.Boolean()
    question = graphene.Field(lambda: QuestionNode)

    def mutate(self, info, id, title, description):
        try:
            with reversion.create_revision():
                question = Question.objects.get(pk=get_id(id))
                question.title = title
                question.description = description
                question.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateQuestion mutation")

            ok = True
        except:
            question = None
            ok = False

        return UpdateQuestion(question=question, ok=ok)

class DeleteQuestion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                question = Question.objects.get(pk=get_id(id))
                question.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteQuestion mutation")

            ok = True
        except:
            ok = False

        return DeleteQuestion(ok=ok)

class Mutation(graphene.ObjectType):
    create_question = CreateQuestion.Field()
    update_question = UpdateQuestion.Field()
    delete_question = DeleteQuestion.Field()

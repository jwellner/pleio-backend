import graphene
import reversion

from core.lib import get_id
from .models import Poll as PollModel
from .entities import Poll

class PollInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)

class CreatePoll(graphene.Mutation):
    class Arguments:
        input = PollInput(required=True)

    ok = graphene.Boolean()
    poll = graphene.Field(lambda: Poll)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                poll = PollModel.objects.create(
                    owner=info.context.user,
                    title=input['title'],
                    description=input['description']
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createPoll mutation")

            ok = True
        except:
            poll = None
            ok = False

        return CreatePoll(poll=poll, ok=ok)

class UpdatePoll(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = PollInput(required=True)

    ok = graphene.Boolean()
    poll = graphene.Field(lambda: Poll)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                poll = PollModel.objects.get(pk=get_id(id))
                poll.title = input['title']
                poll.description = input['description']
                poll.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updatePoll mutation")

            ok = True
        except:
            poll = None
            ok = False

        return UpdatePoll(poll=poll, ok=ok)

class DeletePoll(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                poll = PollModel.objects.get(pk=get_id(id))
                poll.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deletePoll mutation")

            ok = True
        except:
            ok = False

        return DeletePoll(ok=ok)

class Mutation(graphene.ObjectType):
    create_poll = CreatePoll.Field()
    update_poll = UpdatePoll.Field()
    delete_poll = DeletePoll.Field()

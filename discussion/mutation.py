import graphene
import reversion

from core.lib import get_id
from .models import Discussion as DiscussionModel
from .entities import Discussion


class DiscussionInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)


class CreateDiscussion(graphene.Mutation):
    class Arguments:
        input = DiscussionInput(required=True)

    ok = graphene.Boolean()
    discussion = graphene.Field(lambda: Discussion)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                discussion = DiscussionModel.objects.create(
                    owner=info.context.user,
                    title=input['title'],
                    description=input['description']
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createDiscussion mutation")

            ok = True
        except Exception:
            discussion = None
            ok = False

        return CreateDiscussion(discussion=discussion, ok=ok)


class UpdateDiscussion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = DiscussionInput(required=True)

    ok = graphene.Boolean()
    discussion = graphene.Field(lambda: Discussion)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                discussion = DiscussionModel.objects.get(pk=get_id(id))
                discussion.title = input['title']
                discussion.description = input['description']
                discussion.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateDiscussion mutation")

            ok = True
        except Exception:
            discussion = None
            ok = False

        return UpdateDiscussion(discussion=discussion, ok=ok)


class DeleteDiscussion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                discussion = DiscussionModel.objects.get(pk=get_id(id))
                discussion.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteDiscussion mutation")

            ok = True
        except Exception:
            ok = False

        return DeleteDiscussion(ok=ok)


class Mutation(graphene.ObjectType):
    create_discussion = CreateDiscussion.Field()
    update_discussion = UpdateDiscussion.Field()
    delete_discussion = DeleteDiscussion.Field()

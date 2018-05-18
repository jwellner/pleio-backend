import graphene
import reversion

from core.lib import get_id
from .models import Group
from .types import GroupType

class CreateGroup(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupType)

    def mutate(self, info, name, description):
        try:
            with reversion.create_revision():
                group = Group.objects.create(
                    name=name,
                    description=description
                )

                reversion.set_user(info.context.user)
                reversion.set_comment("createGroup mutation")

            ok = True
        except:
            group = None
            ok = False

        return CreateGroup(group=group, ok=ok)

class UpdateGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupType)

    def mutate(self, info, id, name, description):
        try:
            with reversion.create_revision():
                group = Group.objects.get(pk=get_id(id))
                group.name = name
                group.description = description
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateGroup mutation")

            ok = True
        except:
            group = None
            ok = False

        return UpdateGroup(group=group, ok=ok)

class DeleteGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            with reversion.create_revision():
                group = Group.objects.get(pk=get_id(id))
                group.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteGroup mutation")

            ok = True
        except:
            ok = False

        return DeleteGroup(ok=ok)

class Mutation(graphene.ObjectType):
    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()
    delete_group = DeleteGroup.Field()
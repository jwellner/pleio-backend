import graphene
import reversion

from core.lib import get_id
from .models import Group
from .nodes import GroupNode

class GroupInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    is_open = graphene.Boolean(required=True)

class CreateGroup(graphene.Mutation):
    class Arguments:
        input = GroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

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
        input = GroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

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

class JoinGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

    def mutate(self, info, id):
        group = Group.objects.get(pk=get_id(id))
        if group.can_join(info.context.user):
            group.join(info.context.user)
            ok = True
        else:
            ok = False

        return JoinGroup(ok=ok, group=group)

class LeaveGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

    def mutate(self, info, id):
        group = Group.objects.get(pk=get_id(id))

        if info.context.user.is_authenticated:
            group.leave(info.context.user)
            ok = True
        else:
            ok = False

        return LeaveGroup(ok=ok, group=group)

class Mutation(graphene.ObjectType):
    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()
    delete_group = DeleteGroup.Field()
    join_group = JoinGroup.Field()
    leave_group = LeaveGroup.Field()
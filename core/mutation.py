import graphene
import reversion
from django.contrib.contenttypes.models import ContentType
from core.lib import get_id
from .models import Comment, Group, User
from .nodes import Node, GroupNode, CommentNode
from django.db import transaction


class GroupContainsMembers(Exception):
    pass

class NotAuthorized(Exception):
    pass


class CommentInput(graphene.InputObjectType):
    description = graphene.String(required=True)

class CreateComment(graphene.Mutation):
    class Arguments:
        container_id = graphene.ID(required=True)
        input = CommentInput(required=True)

    ok = graphene.Boolean()
    container = graphene.Field(lambda: Node)

    def mutate(self, info, container_id, input):
        parts = container_id.split(':')
        container_type = parts[0].split('.')

        content_type = ContentType.objects.get(app_label=container_type[0], model=container_type[1])
        model_class = content_type.model_class()

        container = model_class.objects.visible(info.context.user).get(id=parts[1])

        if not container.can_comment(info.context.user):
            return CreateComment(ok=False, container=container)

        with reversion.create_revision():
            comment = Comment.objects.create(
                container=container,
                description=input['description'],
                owner=info.context.user
            )

            reversion.set_user(info.context.user)
            reversion.set_comment("createComment mutation")

        ok = True

        return CreateComment(ok=ok, container=container)

class UpdateComment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CommentInput(required=True)

    ok = graphene.Boolean()
    comment = graphene.Field(lambda: CommentNode)

    def mutate(self, info, id, input):
        comment = Comment.objects.get(id=get_id(id))

        if not comment.can_write(info.context.user):
            return UpdateComment(ok=False, comment=comment)

        with reversion.create_revision():
            comment.description = input['description']
            comment.save()

            reversion.set_user(info.context.user)
            reversion.set_comment("updateComment mutation")

        ok = True

        return UpdateComment(ok=ok, comment=comment)

class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        comment = Comment.objects.get(id=get_id(id))

        if not comment.can_write(info.context.user):
            return UpdateComment(ok=False, comment=comment)

        with reversion.create_revision():
            comment.delete()

            reversion.set_user(info.context.user)
            reversion.set_comment("deleteComment mutation")

        ok = True

        return DeleteGroup(ok=ok)

class GroupInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String(required=True)
    is_open = graphene.Boolean(required=True)
    tags = graphene.List(graphene.NonNull(graphene.String))

class CreateGroup(graphene.Mutation):
    class Arguments:
        input = GroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

    def mutate(self, info, input):
        try:
            with reversion.create_revision():
                group = Group.objects.create(
                    name=input['name'],
                    description=input['description'],
                    is_open=input['is_open'],
                    tags=input['tags'],
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

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                group = Group.objects.get(pk=get_id(id))
                if not group.can_change(info.context.user):
                    raise NotAuthorized
                group.name = input['name']
                group.description = input['description']
                group.is_open=input['is_open']
                group.tags=input['tags']
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
                if not group.can_change(info.context.user):
                    raise NotAuthorized
                if group.members.exclude(user=info.context.user).exists():
                    #other members exist, cannot delete group
                    raise GroupContainsMembers
                with transaction.atomic():
                    #owner will only leave group to clear all members from group.
                    #if group.delete fails, owner membership delete will be rollbacked
                    group.leave(info.context.user)
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
            if group.is_open:
                group.join(info.context.user, 'member')
                ok = True
            else:
                group.join(info.context.user, 'pending')
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

class MembershipInput(graphene.InputObjectType):
    userid = graphene.ID(required=True)
    type = graphene.String(required=True)

class ChangeMembershipGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        input = MembershipInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

    def mutate(self, info, id, input):
        try:
            with reversion.create_revision():
                group = Group.objects.get(pk=get_id(id))
                if not group.can_change(info.context.user):
                    raise NotAuthorized
                user = User.objects.get(pk=get_id(input['userid']))
                group.join(user, input['type'])
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("changeMembershipGroup mutation")

            ok = True
        except:
            group = None
            ok = False

        return ChangeMembershipGroup(group=group, ok=ok)

class RemoveMembershipGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        userid = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: GroupNode)

    def mutate(self, info, id, userid):
        try:
            with reversion.create_revision():
                group = Group.objects.get(pk=get_id(id))
                if not group.can_change(info.context.user):
                    raise NotAuthorized
                user = User.objects.get(pk=get_id(userid))
                group.leave(user)
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("removeMembershipGroup mutation")

            ok = True
        except:
            group = None
            ok = False

        return RemoveMembershipGroup(group=group, ok=ok)

class Mutation(graphene.ObjectType):
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()
    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()
    delete_group = DeleteGroup.Field()
    change_membership_group = ChangeMembershipGroup.Field()
    remove_membership_group = RemoveMembershipGroup.Field()
    join_group = JoinGroup.Field()
    leave_group = LeaveGroup.Field()
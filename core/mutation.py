import graphene
import reversion
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from graphql import GraphQLError
from .lib import get_id
from .models import Comment as CommentModel, Group as GroupModel, User as UserModel
from .entities import Entity, Group, Comment
from .constances import *


class CommentInput(graphene.InputObjectType):
    description = graphene.String(required=True)


class CreateComment(graphene.Mutation):
    class Arguments:
        container_id = graphene.ID(required=True)
        input = CommentInput(required=True)

    ok = graphene.Boolean()
    container = graphene.Field(lambda: Entity)

    def mutate(self, info, container_id, input):
        parts = container_id.split(':')
        container_type = parts[0].split('.')

        content_type = ContentType.objects.get(
            app_label=container_type[0],
            model=container_type[1]
            )
        model_class = content_type.model_class()

        container = model_class.objects.visible(
            info.context.user
            ).get(id=parts[1])

        if not container.can_comment(info.context.user):
            raise GraphQLError(COULD_NOT_ADD)

        with reversion.create_revision():
            comment = CommentModel.objects.create(
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
    comment = graphene.Field(lambda: Comment)

    def mutate(self, info, id, input):
        comment = CommentModel.objects.get(id=get_id(id))

        if not comment.can_write(info.context.user):
            raise GraphQLError(COULD_NOT_ADD)

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
        comment = CommentModel.objects.get(id=get_id(id))

        if not comment.can_write(info.context.user):
            raise GraphQLError(COULD_NOT_DELETE)

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
    is_2fa_required = graphene.Boolean(required=True)
    tags = graphene.List(graphene.NonNull(graphene.String))


class CreateGroup(graphene.Mutation):
    class Arguments:
        input = GroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, input):
        ok = False
        group = None

        if not info.context.user.is_authenticated:
            raise GraphQLError(NOT_LOGGED_IN)

        with reversion.create_revision():
            group = GroupModel.objects.create(
                name=input['name'],
                description=input['description'],
                is_open=input['is_open'],
                is_2fa_required=input['is_2fa_required'],
                tags=input['tags'],
            )

            # add creator as group owner
            group.join(info.context.user, 'owner')

            reversion.set_user(info.context.user)
            reversion.set_comment("createGroup mutation")

        ok = True

        return CreateGroup(ok=ok, group=group)


class UpdateGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = GroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, id, input):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not group.can_change(info.context.user):
                raise GraphQLError(USER_NOT_GROUP_OWNER_OR_SITE_ADMIN)

            with reversion.create_revision():
                group.name = input['name']
                group.description = input['description']
                group.is_open = input['is_open']
                group.is_2fa_required = input['is_2fa_required']
                group.tags = input['tags']
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("updateGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return UpdateGroup(ok=ok, group=group)


class DeleteGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        ok = False

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not group.can_change(info.context.user):
                raise GraphQLError(USER_NOT_GROUP_OWNER_OR_SITE_ADMIN)

            with reversion.create_revision():
                if group.members.exclude(user=info.context.user).exists():
                    # other members exist, cannot delete group
                    raise GroupContainsMembers
                with transaction.atomic():
                    # owner will only leave group to clear all members from
                    # group.
                    # if group.delete fails, owner membership delete will be
                    #  rollbacked
                    group.leave(info.context.user)
                    group.delete()

                reversion.set_user(info.context.user)
                reversion.set_comment("deleteGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return DeleteGroup(ok=ok)


class JoinGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, id):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not group.can_join(info.context.user):
                raise GraphQLError(COULD_NOT_ADD)

            if group.is_member(info.context.user):
                raise GraphQLError(COULD_NOT_ADD)

            with reversion.create_revision():
                if group.is_open:
                    group.join(info.context.user, 'member')
                else:
                    group.join(info.context.user, 'pending')

                reversion.set_user(info.context.user)
                reversion.set_comment("joinGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return JoinGroup(ok=ok, group=group)


class LeaveGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, id):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not info.context.user.is_authenticated:
                raise GraphQLError(NOT_LOGGED_IN)

            if not group.is_member(info.context.user):
                raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

            with reversion.create_revision():
                group.leave(info.context.user)

                reversion.set_user(info.context.user)
                reversion.set_comment("leaveGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return LeaveGroup(ok=ok, group=group)


class MembershipInput(graphene.InputObjectType):
    userid = graphene.ID(required=True)
    type = graphene.String(required=True)


class ChangeMembershipGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        input = MembershipInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, id, input):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not group.can_change(info.context.user):
                raise GraphQLError(USER_NOT_GROUP_OWNER_OR_SITE_ADMIN)

            with reversion.create_revision():
                user = UserModel.objects.get(pk=get_id(input['userid']))
                group.join(user, input['type'])
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("changeMembershipGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return ChangeMembershipGroup(ok=ok, group=group)


class RemoveMembershipGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        userid = graphene.ID(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, id, userid):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(id))

            if not group.can_change(info.context.user):
                raise GraphQLError(USER_NOT_GROUP_OWNER_OR_SITE_ADMIN)

            with reversion.create_revision():
                user = UserModel.objects.get(pk=get_id(userid))
                group.leave(user)
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("removeMembershipGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return RemoveMembershipGroup(ok=ok, group=group)


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

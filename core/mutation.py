import requests
import reversion
from django.conf import settings
import graphene, logging, reversion
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from graphql import GraphQLError
from .lib import get_id
from .models import Comment as CommentModel, Group as GroupModel, User as UserModel
from .entities import Entity, Group, Comment, PLUGIN
from .constances import *

logger = logging.getLogger('django')

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

class FeaturedInput(graphene.InputObjectType):
    video = graphene.String()
    image = graphene.String()
    positionY = graphene.Int()


class addGroupInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    icon = graphene.String(required=False)
    featured = graphene.InputField(FeaturedInput)
    is_closed = graphene.Boolean(required=False)
    is_featured = graphene.Boolean(required=False)
    auto_notification = graphene.Boolean(required=False)
    description = graphene.String(required=False)
    richDescription = graphene.JSONString(required=False)
    introduction = graphene.String(required=False)
    welcomeMessage = graphene.String(required=False)
    tags = graphene.List(graphene.String)
    plugins = graphene.List(PLUGIN)

class addGroupPayload(graphene.Mutation):
    class Arguments:
        input = addGroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, input):
        ok = False
        group = None

        if not info.context.user.is_authenticated:
            raise GraphQLError(NOT_LOGGED_IN)

        with reversion.create_revision():
            group = GroupModel.objects.create(
                name=input.get('name'),
                icon=input.get('icon', None),
                is_closed=input.get('is_closed', False),
                is_featured=input.get('is_featured', False),
                auto_notification=input.get('auto_notification', False),
                description=input.get('description', ''),
                richDescription=input.get('rich_description', ''),
                introduction=input.get('introduction', ''),
                welcome_message=input.get('welcome_message', ''),
                tags=input.get('tags', []),
                plugins=input.get('plugins', []),
            )

            if input.get('featured') :
                group.featured_video = input['featured'].get('video', None)
                group.featured_image = input['featured'].get('image', None)
                group.featured_position_y = input['featured'].get('positionY', None)

            group.save()

            # add creator as group owner
            group.join(info.context.user, 'owner')

            reversion.set_user(info.context.user)
            reversion.set_comment("addGroup mutation")

        ok = True

        return addGroupPayload(ok=ok, group=group)

class editGroupInput(graphene.InputObjectType):
    guid = graphene.String(required=True)
    name = graphene.String()
    icon = graphene.String()
    featured = graphene.InputField(FeaturedInput)
    is_closed = graphene.Boolean(required=False)
    is_featured = graphene.Boolean(required=False)
    auto_notification = graphene.Boolean(required=False)
    description = graphene.String(required=False)
    richDescription = graphene.JSONString(required=False)
    introduction = graphene.String(required=False)
    welcomeMessage = graphene.String(required=False)
    tags = graphene.List(graphene.String)
    plugins = graphene.List(PLUGIN)

class editGroupPayload(graphene.Mutation):
    class Arguments:
        input = editGroupInput(required=True)

    ok = graphene.Boolean()
    group = graphene.Field(lambda: Group)

    def mutate(self, info, input):
        ok = False
        group = None

        try:
            group = GroupModel.objects.get(pk=get_id(input.get('guid')))

            if not group.can_change(info.context.user):
                raise GraphQLError(USER_NOT_GROUP_OWNER_OR_SITE_ADMIN)

            with reversion.create_revision():
                group.name = input.get('name', group.name)
                group.icon = input.get('icon', group.icon)
                if input.get('featured') :
                    group.featured_video = input['featured'].get('video', group.featured_video)
                    group.featured_image = input['featured'].get('image', group.featured_video)
                    group.featured_position_y = input['featured'].get('positionY', group.featured_video)

                group.is_closed = input.get('is_closed', group.is_closed)
                group.is_featured = input.get('is_featured', group.is_featured)
                group.auto_notification = input.get('auto_notification', group.auto_notification)
                group.description = input.get('description', group.description)
                group.richDescription = input.get('rich_description', group.richDescription)
                group.introduction = input.get('introduction', group.introduction)
                group.welcome_message = input.get('welcome_message', group.welcome_message)
                group.tags = input.get('tags', group.tags)
                group.plugins = input.get('plugins', group.plugins)
                group.save()

                reversion.set_user(info.context.user)
                reversion.set_comment("editGroup mutation")

            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

        return editGroupPayload(ok=ok, group=group)


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


class editEmailInput(graphene.InputObjectType):
    guid = graphene.String(required=True)
    email = graphene.String(required=True)


class editEmailPayload(graphene.Mutation):

    class Arguments:
        input = editEmailInput(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, input):
        payload = {"email": input.email}

        try:
            token = info.context.session.get("oidc_access_token")
            headers = {"Authorization": "Bearer " + token}
            r = requests.post(settings.OIDC_OP_USER_ME_ENDPOINT + "change_email", data=payload, headers=headers)
            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_CHANGE)

        return editEmailPayload(ok=ok)


class editPasswordInput(graphene.InputObjectType):
    guid = graphene.String(required=True)
    old_password = graphene.String(required=True)
    new_password = graphene.String(required=True)


class editPasswordPayload(graphene.Mutation):

    class Arguments:
        input = editPasswordInput(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, input):
        payload = {"old_password": input.old_password, "new_password": input.new_password}

        try:
            token = info.context.session.get("oidc_access_token")
            headers = {"Authorization": "Bearer " + token}
            r = requests.post(settings.OIDC_OP_USER_ME_ENDPOINT + "change_password", data=payload, headers=headers)
            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_CHANGE)

        return editPasswordPayload(ok=ok)


class editAvatarInput(graphene.InputObjectType):
    guid = graphene.String(required=True)
    avatar = graphene.String(required=True)


class editAvatarPayload(graphene.Mutation):

    class Arguments:
        input = editAvatarInput(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, input):
        files = {
            'avatar': (input.avatar, open(input.avatar, 'rb'))
        }

        try:
            token = info.context.session.get("oidc_access_token")
            headers = {"Authorization": "Bearer " + token}
            r = requests.post(settings.OIDC_OP_USER_ME_ENDPOINT + "change_avatar", files=files, headers=headers)
            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError("Could not change avatar")

        return editAvatarPayload(ok=ok)


class editNameInput(graphene.InputObjectType):
    guid = graphene.String(required=True)
    name = graphene.String(required=True)


class editNamePayload(graphene.Mutation):

    class Arguments:
        input = editNameInput(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, input):
        payload = {"name": input.name}

        try:
            token = info.context.session.get("oidc_access_token")
            headers = {"Authorization": "Bearer " + token}
            r = requests.post(settings.OIDC_OP_USER_ME_ENDPOINT + "change_name", data=payload, headers=headers)
            ok = True
        except GroupModel.DoesNotExist:
            raise GraphQLError(COULD_NOT_CHANGE)

        return editNamePayload(ok=ok)


class Mutation(graphene.ObjectType):
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()
    add_group = addGroupPayload.Field()
    edit_group = editGroupPayload.Field()
    #delete_group = DeleteGroup.Field()
    change_membership_group = ChangeMembershipGroup.Field()
    remove_membership_group = RemoveMembershipGroup.Field()
    join_group = JoinGroup.Field()
    leave_group = LeaveGroup.Field()
    edit_avatar = editAvatarPayload.Field()
    edit_email = editEmailPayload.Field()
    edit_name = editNamePayload.Field()
    edit_password = editPasswordPayload.Field()


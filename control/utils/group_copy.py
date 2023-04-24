from __future__ import absolute_import, unicode_literals

import uuid

import signal_disabler

from celery.utils.log import get_task_logger
from django_tenants.utils import schema_context
from django.utils import timezone
from django.core.files.base import ContentFile

from core.models import Entity, CommentMixin, Comment, GroupMembership, Group, Subgroup, AttachmentMixin
from core.lib import ACCESS_TYPE, access_id_to_acl, get_access_id, get_file_checksum
from core.models.featured import FeaturedCoverMixin
from core.models.rich_fields import ReplaceAttachments
from file.models import FileFolder
from tenants.models import GroupCopy, GroupCopyMapping
from user.models import User

logger = get_task_logger(__name__)


def get_file_field_data(file_field, filename):
    file_data = None
    try:
        file_data = ContentFile(file_field.read())
        file_data.name = filename
    except Exception as e:
        logger.error(e)
    return file_data


class GroupCopyRunner:
    state: GroupCopy

    def __init__(self, state_id=None):
        if state_id:
            self.state = GroupCopy.objects.get(id=state_id)

    @staticmethod
    def file_exists(pk, schema):
        with schema_context(schema):
            return FileFolder.objects.filter(pk=pk).exists()

    def _copy_attachment(self, source_attachment_id, target_owner_id):
        if self.file_exists(source_attachment_id, self.state.target_tenant):
            return source_attachment_id

        if not self.file_exists(source_attachment_id, self.state.source_tenant):
            return None

        with schema_context(self.state.source_tenant):
            source_attachment = FileFolder.objects.get(id=source_attachment_id)
            attachment_contents = get_file_field_data(source_attachment.upload, source_attachment.clean_filename())

        with schema_context(self.state.target_tenant):
            checksum = None
            if source_attachment.is_image():
                checksum = source_attachment.checksum or get_file_checksum(attachment_contents)

            existing_attachment = None
            if checksum:
                existing_attachment = FileFolder.objects \
                    .filter_attachments() \
                    .filter(checksum=checksum,
                            last_scan=source_attachment.last_scan,
                            size=source_attachment.size) \
                    .first()

            if existing_attachment:
                logger.info("used existing attachment %s", existing_attachment.guid)
                return existing_attachment.guid

            new_attachment = FileFolder()
            new_attachment.upload = attachment_contents
            new_attachment.group = None
            new_attachment.owner_id = target_owner_id
            new_attachment.last_scan = source_attachment.last_scan
            new_attachment.last_download = source_attachment.last_download
            new_attachment.blocked = source_attachment.blocked
            new_attachment.block_reason = source_attachment.block_reason
            new_attachment.write_access = [ACCESS_TYPE.user.format(target_owner_id)]
            new_attachment.checksum = checksum
            new_attachment.save()

            logger.info("saved new attachment %s", str(new_attachment.id))
            return new_attachment.guid

    def copy_file_data(self, source_file_id):
        """
        Used in seperate task because of possible heavy load
        """
        with schema_context(self.state.source_tenant):
            source_file = FileFolder.objects.get(id=source_file_id)

        if source_file.upload:
            mapping = self.state.mapping.filter(source_id=source_file_id, entity_type="FileFolder").first()
            with schema_context(self.state.source_tenant):
                file_content = get_file_field_data(source_file.upload, source_file.clean_filename())

            with schema_context(self.state.target_tenant):
                target_file = FileFolder.objects.get(id=mapping.target_id)
                target_file.upload = file_content
                target_file.save()

    def copy_attachments(self, target_entity):
        """
        Copy entity attachments and replace rich_field links
        """
        with schema_context(self.state.source_tenant):
            attachment_ids = target_entity.lookup_attachments()

        attachment_map = ReplaceAttachments()
        for attachment_id in attachment_ids:
            new_attachment_id = self._copy_attachment(attachment_id, target_entity.owner.guid)

            if attachment_id != new_attachment_id:
                attachment_map.append(str(attachment_id), new_attachment_id)

        if hasattr(target_entity, 'replace_attachments'):
            target_entity.replace_attachments(attachment_map)

    def get_or_create_user(self, source_user_id):
        created = False
        with schema_context(self.state.source_tenant):
            source_user = User.objects.with_deleted().get(id=source_user_id)

        with schema_context(self.state.target_tenant):
            user = User.objects.with_deleted().filter(email__iexact=source_user.email).first()

            if not user:
                with signal_disabler.disable():  # prevent auto join in groups
                    user = User.objects.create(
                        name=source_user.name,
                        email=source_user.email,
                        picture=source_user.picture,
                        external_id=source_user.external_id,
                        is_active=source_user.is_active,
                        ban_reason=source_user.ban_reason
                    )
                created = True

        with schema_context('public'):
            GroupCopyMapping.objects.get_or_create(
                copy=self.state,
                entity_type='User',
                source_id=source_user.id,
                target_id=user.id,
                created=created
            )

        return user

    def transform_acl_to_access_id(self, acl):
        access_id = get_access_id(acl)

        if access_id > 10000:
            old_subgroup_id = access_id - 10000
            subgroup_map = GroupCopyMapping.objects.filter(
                copy=self.state,
                entity_type='Subgroup',
                source_id=old_subgroup_id
            ).first()

            if subgroup_map:
                access_id = subgroup_map.target_id.int + 10000
            else:
                access_id = 0

        return access_id

    def create_group(self):
        now = timezone.now()

        with schema_context(self.state.source_tenant):
            group = Group.objects.get(id=self.state.source_id)

        with schema_context(self.state.target_tenant):
            target_group = group
            target_group.name = "Copy: %s" % group.name
            target_group.owner = self.get_or_create_user(group.owner_id)
            target_group.created_at = now
            target_group.updated_at = now
            target_group.is_featured = False
            target_group.is_auto_membership_enabled = False

            if group.featured_image_id:
                target_group.featured_image_id = self._copy_attachment(group.featured_image_id, target_group.owner.guid)
            if group.icon_id:
                target_group.icon_id = self._copy_attachment(group.icon_id, target_group.owner.guid)

            target_group.pk = uuid.uuid4()

            self.copy_attachments(target_group)

            target_group.save()

        self.state.target_id = target_group.id
        self.state.save()

        logger.info("Created group %s", target_group)

    def create_subgroups(self):
        with schema_context(self.state.source_tenant):
            subgroups = list(item for item in Subgroup.objects.filter(group__id=self.state.source_id).all())

        with schema_context(self.state.target_tenant):
            target_group = Group.objects.get(id=self.state.target_id)

            for s in subgroups:
                subgroup_source_id = s.id
                s.group = target_group
                s.pk = None
                s.save()

                GroupCopyMapping.objects.create(
                    copy=self.state,
                    entity_type='Subgroup',
                    source_id=subgroup_source_id,
                    target_id=s.id
                )

        logger.info("Added %i subgroups", len(subgroups))

    def create_members(self):
        with schema_context(self.state.source_tenant):
            if self.state.copy_members:
                memberships = list(item for item in GroupMembership.objects.filter(group__id=self.state.source_id).all())
            else:
                memberships = list(item for item in GroupMembership.objects.filter(group__id=self.state.source_id, type="owner").all())

        with schema_context(self.state.target_tenant):
            target_group = Group.objects.get(id=self.state.target_id)

            for m in memberships:
                m.user = self.get_or_create_user(m.user_id)
                m.group = target_group
                m.pk = None
                m.save()

        logger.info("Inserted %i group members", len(memberships))

        if self.state.copy_members:
            # loop over all members and set subgroup memberships
            subgroup_memberships = []
            with schema_context(self.state.source_tenant):
                for subgroup in Subgroup.objects.filter(group__id=self.state.source_id).all():
                    for member in subgroup.members.all():
                        subgroup_memberships.append({'subgroup_id': subgroup.id, 'user_id': member.id})

            with schema_context(self.state.target_tenant):
                target_group = Group.objects.get(id=self.state.target_id)
                for membership in subgroup_memberships:
                    subgroup_id = GroupCopyMapping.objects.get(
                        copy=self.state,
                        entity_type='Subgroup',
                        source_id=membership.get('subgroup_id')
                    ).target_id

                    subgroup = Subgroup.objects.get(id=subgroup_id)
                    user = self.get_or_create_user(membership.get('user_id'))
                    subgroup.members.add(user)

            logger.info("Added %i subgroup members", len(subgroup_memberships))

    def create_entities(self):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        with schema_context(self.state.source_tenant):
            entities = list(item for item in Entity.objects.filter(group__id=self.state.source_id).select_subclasses())

        with schema_context(self.state.target_tenant):
            target_group = Group.objects.get(id=self.state.target_id)

            connect_parent = []
            connect_best_answers = []
            connect_sub_comments = []
            connect_best_answers = []

            for target_entity in entities:
                source_entity_id = target_entity.id
                parent_source_id = None
                best_answer_source_id = None
                comments = []
                event_attendees = []

                if target_entity.__class__.__name__ in ["Blog", "StatusUpdate", "Task", "FileFolder", "Wiki", "Event", "Question", "Discussion"]:

                    # default entity stuff
                    target_entity.group = target_group
                    target_entity.owner = self.get_or_create_user(target_entity.owner_id)
                    target_entity.is_featured = False
                    target_entity.notifications_created = True
                    target_entity.read_access = access_id_to_acl(target_entity, self.transform_acl_to_access_id(target_entity.read_access))
                    target_entity.write_access = access_id_to_acl(target_entity, self.transform_acl_to_access_id(target_entity.write_access))

                    # specific entity type stuff
                    if isinstance(target_entity, (FeaturedCoverMixin,)) and target_entity.featured_image_id:
                        target_entity.featured_image_id = self._copy_attachment(target_entity.featured_image_id, target_entity.owner.guid)

                    if isinstance(target_entity, (AttachmentMixin,)):
                        self.copy_attachments(target_entity)

                    if target_entity.__class__.__name__ in ["FileFolder", "Wiki", "Event"]:
                        with schema_context(self.state.source_tenant):
                            if target_entity.parent:
                                parent_source_id = target_entity.parent.id
                                target_entity.parent = None

                    if target_entity.__class__.__name__ in ["FileFolder"]:
                        target_entity.thumbnail = None
                        if target_entity.upload:
                            target_entity.upload = None

                    if target_entity.__class__.__name__ in ["Question"]:
                        with schema_context(self.state.source_tenant):
                            if target_entity.best_answer:
                                best_answer_source_id = target_entity.best_answer.id
                                target_entity.best_answer = None

                    if target_entity.__class__.__name__ in ["Event"]:
                        with schema_context(self.state.source_tenant):
                            event_attendees = list(item for item in target_entity.attendees.all())

                    if target_entity.__class__ in CommentMixin.__subclasses__():
                        with schema_context(self.state.source_tenant):
                            comments = list(target_entity.get_flat_comment_list())

                    target_entity.pk = None
                    target_entity.save()

                    GroupCopyMapping.objects.create(
                        copy=self.state,
                        entity_type=target_entity.__class__.__name__,
                        source_id=source_entity_id,
                        target_id=target_entity.id
                    )

                    if target_entity.__class__.__name__ in ["FileFolder"]:
                        # start file copy in seperate process
                        from control.tasks import copy_file_from_source_tenant
                        copy_file_from_source_tenant.delay(self.state.id, source_entity_id)

                    if parent_source_id:
                        connect_parent.append({'entity_id': target_entity.id, 'parent_source_id': parent_source_id})

                    if best_answer_source_id:
                        connect_best_answers.append({'entity_id': target_entity.id, 'best_answer_source_id': best_answer_source_id})

                    for comment in comments:
                        container_source_id = None
                        comment_source_id = comment.id
                        comment.owner = self.get_or_create_user(comment.owner_id)
                        self.copy_attachments(comment)
                        comment.pk = None
                        with schema_context(self.state.source_tenant):
                            if comment.container:
                                if comment.container.__class__.__name__ == 'Comment':  # is subcomment, for now set container to target_entity
                                    container_source_id = comment.container.id

                        comment.container = target_entity

                        with signal_disabler.disable():
                            comment.save()

                        if container_source_id:
                            connect_sub_comments.append({'comment_id': comment.id, 'container_source_id': container_source_id})

                        GroupCopyMapping.objects.create(
                            copy=self.state,
                            entity_type=comment.__class__.__name__,
                            source_id=comment_source_id,
                            target_id=comment.id
                        )

                    # add event attendees
                    for attendee in event_attendees:
                        attendee.event = target_entity
                        attendee.user = self.get_or_create_user(attendee.user_id)
                        attendee.pk = None
                        attendee.save()

            logger.info("Inserted %i entities", len(entities))

            # rebuild parent/child relations
            for connect in connect_parent:
                entity = Entity.objects.get_subclass(id=connect.get('entity_id'))
                parent_id = GroupCopyMapping.objects.get(
                    copy=self.state,
                    entity_type=entity.__class__.__name__,
                    source_id=connect.get('parent_source_id')
                ).target_id
                parent = Entity.objects.get_subclass(id=parent_id)
                if parent != entity:
                    entity.parent = parent
                with signal_disabler.disable():
                    entity.save()

            # rebuild subcomment container relations
            for connect in connect_sub_comments:
                comment = Comment.objects.get(id=connect.get('comment_id'))
                container_id = GroupCopyMapping.objects.get(
                    copy=self.state,
                    entity_type=comment.__class__.__name__,
                    source_id=connect.get('container_source_id')
                ).target_id
                container = Comment.objects.get(id=container_id)
                comment.container = container
                with signal_disabler.disable():
                    comment.save()

            # connect best anwswer
            for connect in connect_best_answers:
                entity = Entity.objects.get_subclass(id=connect.get('entity_id'))
                comment_id = GroupCopyMapping.objects.get(
                    copy=self.state,
                    entity_type='Comment',
                    source_id=connect.get('best_answer_source_id')
                ).target_id
                answer = Comment.objects.get(id=comment_id)
                entity.best_answer = answer
                entity.save()

            # TODO Corrigeer ook suggestedItems

        logger.info("Rebuild %i relations", len(connect_parent) + len(connect_sub_comments) + len(connect_best_answers))

    def run(self, task_id, source_schema, action_user_id, group_id, target_schema=None, copy_members=False):
        if not target_schema:
            target_schema = source_schema

        self.state = GroupCopy.objects.create(
            source_tenant=source_schema,
            target_tenant=target_schema,
            source_id=group_id,
            copy_members=copy_members,
            action_user_id=action_user_id,
            task_id=task_id
        )

        self.create_group()
        self.create_subgroups()
        self.create_members()
        self.create_entities()

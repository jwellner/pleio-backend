import uuid
import logging
from copy import deepcopy

from auditlog.registry import auditlog
from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils import timezone

from core.lib import ACCESS_TYPE, get_access_ids, access_id_to_acl
from core.constances import USER_ROLES
from core.models.featured import FeaturedCoverMixin
from core.utils.convert import tiptap_to_text
from .tags import TagsModel
from .rich_fields import AttachmentMixin, ReplaceAttachments
from core.widget_resolver import WidgetSerializer

logger = logging.getLogger(__name__)


class GroupManager(models.Manager):
    def visible(self, user):
        if not user.is_authenticated:
            return self.get_queryset().exclude(is_hidden=True)

        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return self.get_queryset()

        hidden_groups_where_users_isnt_a_member = Q()
        hidden_groups_where_users_isnt_a_member.add(Q(is_hidden=True), Q.AND)
        hidden_groups_where_users_isnt_a_member.add(~Q(members__user=user), Q.AND)

        return self.get_queryset().exclude(hidden_groups_where_users_isnt_a_member)


class Group(TagsModel, FeaturedCoverMixin, AttachmentMixin):
    class Meta:
        ordering = ['name']

    objects = GroupManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('user.User', on_delete=models.PROTECT)

    name = models.CharField(max_length=200)

    rich_description = models.JSONField(null=True, blank=True)

    introduction = models.TextField(default='')
    is_introduction_public = models.BooleanField(default=False)
    welcome_message = models.TextField(default='')
    required_fields_message = models.TextField(default='')

    icon = models.ForeignKey(
        'file.FileFolder',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='group_icon'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    is_featured = models.BooleanField(default=False)
    featured_image = models.ForeignKey(
        'file.FileFolder',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='group_featured_image'
    )

    is_closed = models.BooleanField(default=False)
    is_membership_on_request = models.BooleanField(default=False)
    is_leaving_group_disabled = models.BooleanField(default=False)
    is_auto_membership_enabled = models.BooleanField(default=False)
    is_submit_updates_enabled = models.BooleanField(default=True)

    is_hidden = models.BooleanField(default=False)

    auto_notification = models.BooleanField(default=False)

    plugins = ArrayField(models.CharField(
        max_length=256), blank=True, default=list)

    content_presets = models.JSONField(default=dict)

    widget_repository = models.JSONField(null=True, default=list)

    def __str__(self):
        return f"Group[{self.name}]"

    def is_member(self, user):
        if not user.is_authenticated:
            return False

        try:
            return self.members.filter(user=user).exists()
        except ObjectDoesNotExist:
            return False

    def is_full_member(self, user):
        if not user.is_authenticated:
            return False

        try:
            return self.members.filter(
                user=user,
                type__in=['admin', 'owner', 'member']
            ).exists()
        except ObjectDoesNotExist:
            return False

    def is_pending_member(self, user):
        if not user.is_authenticated:
            return False

        return self.members.filter(user=user, type='pending').exists()

    def can_write(self, user):
        if not user.is_authenticated:
            return False

        if user.has_role(USER_ROLES.ADMIN):
            return True

        if user == self.owner:
            return True

        return self.members.filter(user=user, type__in=['admin', 'owner']).exists()

    def join(self, user, member_type='member'):
        # pylint: disable=unused-variable
        already_member = self.is_full_member(user)

        obj, created = self.members.update_or_create(
            user=user,
            defaults={
                'type': member_type,
                'is_notifications_enabled': self.auto_notification
            }
        )

        # send welcome message for new members
        if obj.type == 'member' and not already_member and self.welcome_message:
            from core.mail_builders.group_welcome import schedule_group_welcome_mail
            schedule_group_welcome_mail(group=self,
                                        user=user)

        return obj

    def leave(self, user):
        if self.subgroups:
            for subgroup in self.subgroups.all():
                if user in subgroup.members.all():
                    subgroup.members.remove(user)
        try:
            return self.members.get(user=user).delete()
        except ObjectDoesNotExist:
            return False

    def set_member_is_notifications_enabled(self, user, is_notifications_enabled):
        member = self.members.filter(user=user).first()
        if member:
            member.is_notifications_enabled = is_notifications_enabled
            member.save()
            return True
        return False

    def set_member_is_notification_direct_mail_enabled(self, user, is_notification_direct_mail_enabled):
        member = self.members.filter(user=user).first()
        if member:
            member.is_notification_direct_mail_enabled = is_notification_direct_mail_enabled
            member.save()
            return True
        return False

    def set_member_is_notification_push_enabled(self, user, is_notification_push_enabled):
        member = self.members.filter(user=user).first()
        if member:
            member.is_notification_push_enabled = is_notification_push_enabled
            member.save()
            return True
        return False

    def save(self, *args, **kwargs):
        self.update_entity_access()
        super(Group, self).save(*args, **kwargs)

    def update_entity_access(self):
        """
        Update Entity read_access when group is set to 'Closed'
        """
        if self.is_closed:
            # to prevent cyclic import
            Entity = apps.get_model('core', 'Entity')

            assert self.id, "Group should have an ID when update read-access"

            filters = Q()
            filters.add(Q(group__id=self.id), Q.AND)
            filters.add(Q(read_access__overlap=list([ACCESS_TYPE.public, ACCESS_TYPE.logged_in])), Q.AND)

            entities = Entity.objects.filter(filters)
            for entity in entities:
                if ACCESS_TYPE.public in entity.read_access:
                    entity.read_access.remove(ACCESS_TYPE.public)
                if ACCESS_TYPE.logged_in in entity.read_access:
                    entity.read_access.remove(ACCESS_TYPE.logged_in)
                if not ACCESS_TYPE.group.format(self.id) in entity.read_access:
                    entity.read_access.append(ACCESS_TYPE.group.format(self.id))
                entity.save()

    @property
    def guid(self):
        return str(self.id)

    @property
    def url(self):
        return "/groups/view/{}/{}".format(self.guid, slugify(self.name))

    @property
    def type_to_string(self):
        return 'group'

    @property
    def rich_fields(self):
        return [field for field in self.attachments_from_rich_fields()]

    def attachments_from_rich_fields(self):
        if self.rich_description:
            yield self.rich_description
        if self.introduction:
            yield self.introduction
        for widget in self.widget_repository or []:
            yield from WidgetSerializer(widget).rich_fields()

    def lookup_attachments(self):
        yield from super().lookup_attachments()
        for widget in self.widget_repository or []:
            yield from WidgetSerializer(widget).attachments()
        if self.icon:
            yield self.icon.guid

    def replace_attachments(self, attachment_map: ReplaceAttachments):
        super().replace_attachments(attachment_map)

        if self.introduction:
            self.introduction = attachment_map.replace(self.introduction)

        for widget_id, widget in enumerate(self.widget_repository):
            if 'settings' not in widget or not widget.get('settings'):
                continue
            for setting_id, setting in enumerate(widget['settings']):
                attachment_id = setting.get('attachmentId')
                if attachment_map.has_attachment(attachment_id):
                    setting['attachmentId'] = attachment_map.translate(attachment_id)
                if setting['key'] == 'richDescription' or setting.get('richDescription'):
                    setting['richDescription'] = attachment_map.replace(setting['richDescription'] or setting['value'])
                    setting['value'] = None
                self.widget_repository[widget_id]['settings'][setting_id] = setting

    def map_rich_text_fields(self, callback):
        # Welcome message is for email, should be treated differently
        # self.welcome_message = callback(self.welcome_message)
        self.rich_description = callback(self.rich_description)
        self.introduction = callback(self.introduction)

        new_widgets = []
        for widget in self.widget_repository:
            serializer = WidgetSerializer(widget)
            serializer.map_rich_fields(callback)
            new_widgets.append(serializer.serialize())
        self.widget_repository = new_widgets

    def search_read_access(self):
        return [ACCESS_TYPE.public]

    @property
    def description(self):
        return tiptap_to_text(self.rich_description)

    def disk_size(self):
        from file.models import FileFolder, FileReference
        from core.models import Entity

        file_folder_size = 0
        attachment_size = 0

        ids = FileFolder.objects.filter_files().filter(group=self.id).values_list('id', flat=True)
        f = FileFolder.objects.filter(id__in=ids).aggregate(total_size=models.Sum('size'))
        if f.get('total_size', 0):
            file_folder_size = f.get('total_size', 0)

        entities = Entity.objects.filter(group=self).values_list('id', flat=True)
        e = FileReference.objects \
            .filter(container_fk__in=[*entities, self.id]) \
            .exclude(file__id__in=ids) \
            .aggregate(total_size=models.Sum('file__size'))
        if e.get('total_size', 0):
            attachment_size = e.get('total_size', 0)

        return file_folder_size + attachment_size

    def serialize(self):
        return {
            'name': self.name,
            'ownerGuid': self.owner.guid if self.owner else '',
            'richDescription': self.rich_description or '',
            'intro': self.introduction or '',
            'isIntroductionPublic': self.is_introduction_public,
            'welcomeMessage': self.welcome_message or '',
            'requiredProfileFieldsMessage': self.required_fields_message or '',
            'icon': self.icon_id,
            'isFeatured': self.is_featured,
            'featured': self.serialize_featured(),
            'isClosed': self.is_closed,
            'isMembershipOnRequest': self.is_membership_on_request,
            'isLeavingGroupDisabled': self.is_leaving_group_disabled,
            'isAutoMembershipEnabled': self.is_auto_membership_enabled,
            'isSubmitUpdatesEnabled': self.is_submit_updates_enabled,
            'isHidden': self.is_hidden,
            'autoNotification': self.auto_notification,
            'plugins': self.plugins,
            'defaultTags': sorted(self.content_presets.get('defaultTags') or []),
            'defaultTagCategories': deepcopy(self.content_presets.get('defaultTagCategories') or []),
            'widgets': deepcopy(self.widget_repository),
            'tags': sorted(self.tags),
            'tagCategories': self.category_tags,
        }

    def get_read_access(self):
        result = set()
        for acid in get_access_ids(self):
            result.update(access_id_to_acl(self, acid['id']))
        return [*result]


class GroupMembership(models.Model):
    class Meta:
        unique_together = ('user', 'group')
        ordering = ['group']

    MEMBER_TYPES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('pending', 'Pending')
    )

    user = models.ForeignKey(
        'user.User',
        related_name='memberships',
        on_delete=models.PROTECT
    )
    type = models.CharField(
        max_length=10,
        choices=MEMBER_TYPES,
        default='member'
    )
    group = models.ForeignKey(
        'core.Group',
        related_name='members',
        on_delete=models.CASCADE
    )

    is_notifications_enabled = models.BooleanField(default=True)
    is_notification_direct_mail_enabled = models.BooleanField(default=False)
    is_notification_push_enabled = models.BooleanField(default=False)

    admin_weight = models.IntegerField(
        default=100,
        null=False,
    )

    def __str__(self):
        return "GroupMembership[{}:{}:{}]".format(
            self.user.email,
            self.type,
            self.group.name
        )

    def save(self, *args, **kwargs):
        self.admin_weight = self.get_admin_weight()
        super().save(*args, **kwargs)

    def get_admin_weight(self):
        """
         Weight of the membership on administration pages. Owner on top.
        """
        sort_index = {'owner': 1, 'admin': 2, 'member': 3}
        return sort_index.get(self.type) or 100

    def index_instance(self):
        return self.user

    created_at = models.DateTimeField(default=timezone.now)


class GroupInvitation(models.Model):
    class Meta:
        unique_together = ('invited_user', 'group')

    group = models.ForeignKey(
        'core.Group',
        related_name='invitations',
        on_delete=models.CASCADE
    )
    invited_user = models.ForeignKey(
        'user.User',
        related_name='invitation',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    email = models.EmailField(max_length=255, blank=True, null=True)

    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"GroupInvitation[]"


class Subgroup(models.Model):
    """
    A group of users within a group
    """

    name = models.CharField(max_length=512)
    members = models.ManyToManyField('user.User', related_name='subgroups')
    group = models.ForeignKey('core.Group', related_name='subgroups', on_delete=models.CASCADE)

    @property
    def access_id(self):
        return 10000 + self.id

    def __str__(self):
        return f"Subgroup[{self.name}]"


class GroupProfileFieldSetting(models.Model):
    """
    Group settings for ProfileField
    """
    group = models.ForeignKey('core.Group', related_name='profile_field_settings', on_delete=models.CASCADE)
    profile_field = models.ForeignKey('core.ProfileField', related_name='group_settings', on_delete=models.CASCADE)
    show_field = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)

    def clean(self):
        if self.profile_field.field_type == 'html_field' and self.show_field:
            raise ValidationError("Long text fields are not allowed to display on the member page.")

    def save(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        self.full_clean()
        super(GroupProfileFieldSetting, self).save(*args, **kwargs)


auditlog.register(Group)
auditlog.register(GroupMembership)
auditlog.register(Subgroup)

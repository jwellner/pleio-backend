import uuid
from core import config
from core.constances import USER_ROLES
from core.data.paginate_result import PaginateResult
from core.models import UserProfile, ProfileField, UserProfileField, SiteAccessRequest
from datetime import timedelta
from django.db.models import Case, Q, Value, When
from django.db.models.signals import post_save
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone


class Manager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_active=False, name="Verwijderde gebruiker")

    def with_deleted(self):
        return super().get_queryset()

    def visible(self, user):
        # pylint: disable=unused-argument
        """
        User is always visible. User property access is handled in user resolver.
        """
        return self.get_queryset()

    def create_user(
            self,
            email,
            name,
            password=None,
            external_id=None,
            is_active=False,
            is_superadmin=False,
            picture=None,
            is_government=False,
            has_2fa_enabled=False):
        # pylint: disable=too-many-arguments
        # pylint: disable=unused-argument
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name
        )

        if password:
            user.set_password(password)

        if external_id:
            user.external_id = external_id

        if picture:
            user.picture = picture

        if is_government:
            user.is_government = is_government

        if has_2fa_enabled:
            user.has_2fa_enabled = has_2fa_enabled

        if is_superadmin:
            user.is_superadmin = True

        if is_active:
            user.is_active = True

        user.save(using=self._db)

        # Site access request can only be used once
        try:
            SiteAccessRequest.objects.get(email=email).delete()
        except Exception:
            pass

        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(
            email=self.normalize_email(email),
            name=name,
            password=password
        )

        user.is_superadmin = True
        user.is_active = True
        user.save(using=self._db)

        return user

    def get_filtered_users(self, q=None, role=None, isDeleteRequested=None, isBanned=False, last_online_before=None):
        # pylint: disable=too-many-arguments

        users = User.objects.all().order_by('name')

        if isBanned:
            users = users.filter(is_active=False)
        else:
            users = users.filter(is_active=True)

        if q:
            users = users.filter(
                Q(name__icontains=q) |
                Q(email__icontains=q) |
                Q(id__iexact=q)
            )

        if last_online_before:
            users = users.filter(_profile__last_online__lt=last_online_before)

        if role is not None and hasattr(USER_ROLES, role.upper()):
            ROLE_FILTER = getattr(USER_ROLES, role.upper())
            users = users.filter(roles__contains=[ROLE_FILTER])

        if isDeleteRequested is not None:
            users = users.filter(is_delete_requested=isDeleteRequested)

        return users

    def get_unmentioned_users(self, user_ids, instance):
        if not user_ids:
            return self.get_queryset().none()

        return self.get_queryset() \
            .filter(id__in=user_ids) \
            .filter(~Q(notifications__verb='mentioned', notifications__action_object_object_id=instance.id))

    def get_upcoming_birthday_users(self, profileFieldGuid, user, start_date, end_date, offset=0, limit=20):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals

        profile_field = ProfileField.objects.get_date_field(profileFieldGuid)

        index = start_date
        filter_dates = Q()
        while index < end_date:
            filter_dates.add(
                Q(
                    value_date__month=index.month,
                    value_date__day=index.day
                ),
                Q.OR
            )
            index += timedelta(days=1)

        user_profile_fields = UserProfileField.objects.visible(user).filter(
            Q(profile_field=profile_field) &
            filter_dates
        ).order_by(
            Case(
                When(value_date__month__gte=start_date.month, then=Value(0)),
                When(value_date__month__lt=start_date.month, then=Value(1)),
            ),
            'value_date__month',
            'value_date__day',
            'value_date__year',
        )

        ids = []
        selection = user_profile_fields[offset:offset+limit]
        for item in selection:
            ids.append(item.user_profile.user.guid)

        users = User.objects.filter(id__in=ids)

        # use birthday ordering on objects
        id_dict = {d.guid: d for d in users}
        sorted_users = [id_dict[id] for id in ids]

        return PaginateResult(user_profile_fields.count(), sorted_users)


class User(AbstractBaseUser):
    objects = Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)

    external_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    picture = models.URLField(blank=True, null=True)
    is_government = models.BooleanField(default=False)
    has_2fa_enabled = models.BooleanField(default=False)
    is_delete_requested = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=100, default="", blank=True)

    roles = ArrayField(models.CharField(max_length=256), blank=True, default=list)

    # for profile sync matching
    custom_id = models.CharField(
        max_length=200,
        unique=True,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    REQUIRED_FIELDS = ['name']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    @property
    def type_to_string(self):
        return 'user'

    @property
    def url(self):
        return "/user/{}/profile".format(self.guid)

    @property
    def icon(self):
        if self.profile.picture_file:
            return self.profile.picture_file.thumbnail_url
        return self.picture

    def search_read_access(self):
        return ['logged_in']

    @property
    def is_staff(self):
        return self.is_superadmin

    def has_role(self, role):
        # pylint: disable=unused-argument
        if self.is_superadmin:
            return True

        return role in list(self.roles)

    def has_perm(self, perm, obj=None):
        # pylint: disable=unused-argument
        return self.is_superadmin

    def has_module_perms(self, app_label):
        # pylint: disable=unused-argument
        return self.is_superadmin

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def get_language(self):
        if self.profile.language and ((self.profile.language == config.LANGUAGE) or (self.profile.language in config.EXTRA_LANGUAGES)):
            return self.profile.language
        return config.LANGUAGE

    def as_mailinfo(self):
        return {
            'name': self.name,
            'email': self.email,
            'language': self.get_language(),
        }

    @property
    def guid(self):
        return str(self.id)

    @property
    def profile(self):
        try:
            return self._profile
        except UserProfile.DoesNotExist:
            if not settings.RUN_AS_ADMIN_APP:
                return UserProfile.objects.create(
                    user=self
                )

    @property
    def is_profile_complete(self):
        fields = ProfileField.objects.filter(is_mandatory=True).all()

        incomplete = 0

        for field in fields:
            user_profile_field = UserProfileField.objects.filter(profile_field=field, user_profile=self.profile).first()
            if user_profile_field and user_profile_field.value == '':
                incomplete += 1
            if not user_profile_field:
                incomplete += 1

        return incomplete == 0

    def delete(self, using='', keep_parents=False):
        self.is_active = False
        self.email = "%s@deleted" % self.guid
        self.name = "Verwijderde gebruiker"
        self.external_id = None
        self.custom_id = None
        self.picture = None
        self.is_government = False
        self.has_2fa_enabled = False
        self.ban_reason = "Deleted"
        self.is_delete_requested = False
        self.is_superadmin = False
        self.roles = []

        # delete user profile data
        try:
            self._profile.delete()
        except UserProfile.DoesNotExist:
            pass

        # delete memberships and notifications
        self.memberships.all().delete()
        self.subgroups.all().delete()
        self.notifications.all().delete()
        self.invitation.all().delete()
        self.annotations.all().delete()

        self.save()

        return True

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    if not settings.RUN_AS_ADMIN_APP and created:
        UserProfile.objects.create(user=instance)

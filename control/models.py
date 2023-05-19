import django_filters
import uuid

from enum import Enum
from celery import signature, chain
from django.db import models
from django.forms import Select, TextInput
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_tenants.utils import schema_context

from core.lib import tenant_schema
from tenants.models import Client


class SiteFilter(django_filters.FilterSet):
    # pylint: disable=keyword-arg-before-vararg

    def __init__(self, data=None, *args, **kwargs):
        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()

            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)

    domain = django_filters.CharFilter(
        field_name='domains__domain',
        lookup_expr='icontains',
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Domein'})
    )

    is_active = django_filters.BooleanFilter(
        widget=Select(attrs={'class': 'form-control'},
                      choices=[(True, 'Active sites'), (False, 'Disabled sites')]),
        initial=True
    )

    class Meta:
        model = Client
        fields = ['domain', 'is_active']


class TaskManager(models.Manager):

    def create_task(self, name, arguments=None, **kwargs):
        task_id = uuid.uuid4()
        chain(
            signature(name, arguments).set(task_id=str(task_id)),
            signature('control.tasks.followup_task_complete')
        ).apply_async()

        task = self.model(
            task_id=task_id,
            state='PENDING',
            name=name,
            arguments=arguments,
            **kwargs,
        )

        task.save()

        return task


class Task(models.Model):
    STATE_TYPES = (
        ('PENDING', 'PENDING'),
        ('STARTED', 'STARTED'),
        ('RETRY', 'RETRY'),
        ('FAILURE', 'FAILURE'),
        ('SUCCESS', 'SUCCESS'),
    )

    objects = TaskManager()

    class Meta:
        ordering = ['-created_at']

    author = models.ForeignKey('user.User', null=True, on_delete=models.CASCADE, related_name='tasks')
    client = models.ForeignKey('tenants.Client', null=True, on_delete=models.CASCADE, related_name='tasks')

    task_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    origin = models.CharField(max_length=255, default='')
    followup = models.CharField(max_length=255, null=True)

    arguments = models.JSONField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)

    state = models.CharField(
        max_length=16,
        choices=STATE_TYPES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def run_followup(self):
        try:
            if not self.followup:
                return

            followup = import_string(self.followup)
            followup.delay(self.id)
        except Exception:
            pass


class AccessCategory(Enum):
    SITE_BACKUP = _("Site backup")


class AccessLogManager(models.Manager):
    """Separate Manager for testing purposes. """


class AccessLog(models.Model):
    objects = AccessLogManager()

    class Meta:
        ordering = ('-created_at',)

    class AccessTypes(models.TextChoices):
        CREATE = 'create', pgettext_lazy("Past Perfect", "Created")
        READ = 'read', pgettext_lazy("Past Perfect", "Read")
        DOWNLOAD = 'download', pgettext_lazy("Past Perfect", "Downloaded")
        UPDATE = 'update', pgettext_lazy("Past Perfect", "Updated")
        DELETE = 'delete', pgettext_lazy("Past Perfect", "Deleted")

    created_at = models.DateTimeField(default=timezone.now)
    category = models.CharField(max_length=256)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    item_id = models.CharField(max_length=256)
    type = models.CharField(max_length=128, choices=AccessTypes.choices)
    site = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, default=None, null=True, blank=True)

    @staticmethod
    def custom_category(category, suffix):
        return "%s:%s" % (category.name, suffix)

    @property
    def type_label(self):
        return AccessLog.AccessTypes(self.type).label


class ElasticsearchStatusManager(models.Manager):

    def cleanup(self, **filter_kwargs):
        existing = self.get_queryset().filter(**filter_kwargs)
        for item in existing[2:]:
            item.delete()

    def previous(self, client, reference_date):
        qs = self.get_queryset()
        qs = qs.filter(client=client, created_at__lt=reference_date)
        return qs.first()

    def next(self, client, reference_date):
        qs = self.get_queryset().order_by('created_at')
        qs = qs.filter(client=client, created_at__gt=reference_date)
        return qs.first()


class ElasticsearchStatus(models.Model):
    class Meta:
        ordering = ('-created_at',)

    objects = ElasticsearchStatusManager()

    client = models.ForeignKey('tenants.Client', null=True, on_delete=models.CASCADE, related_name='elasticsearch_status')
    index_status = models.JSONField(null=True)
    access_status = models.JSONField(null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def index_status_summary(self):
        if self.index_status.get('result'):
            return _("Index not up to date")
        if 'message' in self.index_status:
            return self.index_status['message']
        return ""

    def access_status_summary(self):
        if self.access_status.get('result'):
            return _("Index may not be accessible")
        if 'message' in self.access_status:
            return self.access_status['message']
        return ""


class FileOperationManager(models.Manager):

    def add_log(self, operation, result):
        current_schema = tenant_schema()

        with schema_context('public'):
            self.create(client=Client.objects.get(schema_name=current_schema),
                        operation=operation,
                        result=result)


class FileOperationLog(models.Model):
    class Meta:
        ordering = ('operation', '-created_at',)

    objects = FileOperationManager()

    created_at = models.DateTimeField(default=timezone.now)
    client = models.ForeignKey('tenants.Client', null=True, on_delete=models.CASCADE, related_name='file_operation_log')
    operation = models.CharField(max_length=255)
    result = models.JSONField(default=dict)

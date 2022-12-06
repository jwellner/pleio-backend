import celery
import django_filters

from django.db import models
from django.forms import Select, TextInput
from django.utils.module_loading import import_string
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
        remote_task = celery.current_app.send_task(name, arguments)

        task = self.model(
            task_id=remote_task.id,
            state=remote_task.state,
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

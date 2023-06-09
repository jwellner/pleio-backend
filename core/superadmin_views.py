import json
import logging
import os

from auditlog.models import LogEntry
from datetime import timedelta

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.module_loading import import_string
from django.views import View
from django.utils import timezone
from celery.result import AsyncResult

from core.constances import OIDC_PROVIDER_OPTIONS
from core.elasticsearch import elasticsearch_status_report
from core.forms import MeetingsSettingsForm, ProfileSetForm
from core.models import Group, ProfileSet, SiteStat
from core.models.agreement import CustomAgreement
from core.tasks import replace_domain_links, elasticsearch_rebuild_for_tenant, elasticsearch_index_data_for_tenant
from core.lib import tenant_schema, is_valid_domain
from core.superadmin.forms import AuditLogFilter, CustomAgreementForm, SettingsForm, ScanIncidentFilter, OptionalFeaturesForm, SupportContractForm
from control.tasks import copy_group
from core.tasks.elasticsearch_tasks import all_indexes
from file.models import ScanIncident, FileFolder
from tenants.models import Client, GroupCopy

logger = logging.getLogger(__name__)


class SuperAdminView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superadmin

    def handle_no_permission(self):
        return redirect('/')


class Dashboard(SuperAdminView):
    http_method_names = ['get']

    def get(self, request):

        try:
            db_usage = SiteStat.objects.filter(stat_type='DB_SIZE').latest('created_at').value
        except Exception:
            db_usage = 0

        try:
            file_usage = SiteStat.objects.filter(stat_type='DISK_SIZE').latest('created_at').value
        except Exception:
            file_usage = 0

        context = {
            'stats': {
                'db_usage': db_usage,
                'file_usage': file_usage
            }
        }

        return render(request, 'superadmin/home.html', context)


class Settings(SuperAdminView):
    http_method_names = ['post', 'get']

    def get_context(self):
        return {
            'constants': {
                'OIDC_PROVIDER_OPTIONS': OIDC_PROVIDER_OPTIONS,
            },
        }

    def post(self, request):
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/superadmin/settings')

        context = self.get_context()
        context['form'] = form

        return render(request, 'superadmin/settings.html', context)

    def get(self, request):
        context = self.get_context()

        return render(request, 'superadmin/settings.html', context)


class ScanLog(SuperAdminView):
    http_method_names = ['get']

    def get(self, request):
        filtered_qs = ScanIncidentFilter(request.GET, queryset=ScanIncident.objects.all())
        form = filtered_qs.form
        qs = filtered_qs.qs[:100]

        context = {
            'qs': qs,
            'form': form,
            'first_scanned_file': FileFolder.objects.order_by('last_scan').first(),
            'last_scanned_file': FileFolder.objects.order_by('-last_scan').first(),
            'total_files': FileFolder.objects.count()
        }

        return render(request, 'superadmin/scanlog.html', context)


class AuditLog(SuperAdminView):
    http_method_names = ['get']

    def get(self, request):
        page_param = request.GET.get('page', '1')
        page = max(int(page_param) - 1, 0) if page_param.isnumeric() else 0
        page_size = 100
        offset = page * page_size

        filtered_qs = AuditLogFilter(request.GET, LogEntry.objects.all())
        logs = filtered_qs.qs[offset:offset + page_size + 1]  # grab one extra so we can check if there are more pages
        for log in logs:
            log.changes_obj = json.loads(log.changes)

        next_page = request.GET.copy()
        next_page['page'] = page + 2
        previous_page = request.GET.copy()
        previous_page['page'] = page

        has_next = len(logs) > page_size
        has_previous = page > 0

        context = {
            'logs': logs[:page_size],
            'form': filtered_qs.form,
            'previous_page': previous_page.urlencode() if has_previous else None,
            'next_page': next_page.urlencode() if has_next else None
        }

        return render(request, 'superadmin/auditlog.html', context)


class GroupCopyView(SuperAdminView):
    http_method_names = ['post', 'get']

    def get(self, request):
        sites = []
        for client in Client.objects.exclude(schema_name__in=['public', tenant_schema()]):
            sites.append({'schema': client.schema_name, 'domain': client.get_primary_domain().domain})

        tasks = GroupCopy.objects.filter(source_tenant=tenant_schema()).exclude(task_state__in=["SUCCESS", "FAILURE"])
        for task in tasks:
            remote_task = AsyncResult(task.task_id)
            task.task_state = remote_task.state

            if remote_task.successful():
                task.task_response = remote_task.result
            elif remote_task.failed():
                task.task_response = {
                    "error": str(remote_task.result)
                }
            else:
                # timeout task after 1 day
                if task.created_at < (timezone.now() - timedelta(days=1)):
                    task.task_state = "FAILURE"
                    task.task_response = "TIMEOUT"
            task.save()

        items = GroupCopy.objects.filter(source_tenant=tenant_schema()).all()

        context = {
            'groups': Group.objects.all(),
            'sites': sites,
            'items': items
        }

        return render(request, 'superadmin/group_copy.html', context)

    def post(self, request):
        try:
            assert request.POST.get("group"), "Provide group"
            #assert request.POST.get("target_tenant"), "Provide target tenant"

            group_id = request.POST.get("group")
            target_tenant = request.POST.get("target_tenant")
            action_user_id = request.user.id
            copy_members = request.POST.get("copy_members") == "1"
            copy_group.delay(tenant_schema(), action_user_id, group_id, target_tenant, copy_members)
            messages.success(request, f"Copy group for {group_id} to {target_tenant} started.")

        except AssertionError as e:
            messages.error(request, f"Error: {e}")

        return redirect('/superadmin/group_copy')


class HandleViewTasksPage(SuperAdminView):
    http_method_names = ['get']

    def get(self, request):
        # pylint: disable=unused-argument
        context = {}

        try:
            context["es_report"] = elasticsearch_status_report()
        except Exception as e:
            messages.error(request, str(e))

        return render(request, 'superadmin/tasks.html', context)


class HandleScheduleCronTask(SuperAdminView):
    http_method_names = ['post']

    def post(self, request):
        try:
            method = import_string(request.POST.get("subtask"))
            method.delay(schema_name=tenant_schema())
            messages.success(request, "Scheduled task %s" % request.POST.get("subtask"))
        except Exception as e:
            messages.error(request, "%s at %s: %s" % (e.__class__.__name__, request.POST.get("subtask"), e))
        return redirect('/superadmin/tasks')


class HandleUpdateLinksTask(SuperAdminView):
    http_method_names = ['post']

    def post(self, request):
        current_domain = request.tenant.get_primary_domain().domain
        replace_domain = request.POST.get("replace_domain") if request.POST.get("replace_domain") else current_domain
        if not is_valid_domain(replace_domain):
            messages.error(request, f"The domain {replace_domain} is not a valid domain")
        elif current_domain == replace_domain:
            messages.error(request, "Please provide the domain name to replace")
        else:
            replace_domain_links.delay(tenant_schema(), replace_domain)
            messages.success(request, f"Replace links for {replace_domain} started.")
        return redirect('/superadmin/tasks')


class HandleElasticsearchTask(SuperAdminView):
    # pylint: disable=protected-access
    http_method_names = ['post']

    def post(self, request):
        task = request.POST.get("task", False)
        index_name = request.POST.get("index_name")
        if task == "elasticsearch_rebuild":
            if index_name in [i._name for i in all_indexes()]:
                elasticsearch_rebuild_for_tenant.delay(tenant_schema(), index_name=index_name)
                messages.success(request, 'Elasticsearch rebuild started for %s' % index_name)
            elif not index_name:
                elasticsearch_rebuild_for_tenant.delay(tenant_schema())
                messages.success(request, 'Elasticsearch rebuild started')
            else:
                messages.error(request, 'Specify an index to process')
        elif task == "elasticsearch_update":
            if index_name in [i._name for i in all_indexes()]:
                elasticsearch_index_data_for_tenant.delay(tenant_schema(), index_name=index_name)
                messages.success(request, 'Elasticsearch update started for %s' % index_name)
            elif not index_name:
                elasticsearch_index_data_for_tenant.delay(tenant_schema())
                messages.success(request, 'Elasticsearch update started')
            else:
                messages.error(request, 'Specify an index to process')
        else:
            messages.error(request, "Invalid command %s" % task)
        return redirect('/superadmin/tasks')


class SupportContract(SuperAdminView):
    http_method_names = ['post', 'get']

    def post(self, request):
        form = SupportContractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/superadmin/support_contract')

        context = {'form': form}

        return render(request, 'superadmin/support_contract.html', context)

    def get(self, request):
        return render(request, 'superadmin/support_contract.html')


@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def agreements(request):
    if request.method == 'POST':
        form = CustomAgreementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Custom agreement saved')
            form = CustomAgreementForm()
    else:
        form = CustomAgreementForm()
    agreements = CustomAgreement.objects.all()
    custom_agreements = []
    for agreement in agreements:
        custom_agreements.append({
            'name': agreement.name,
            'file_name': os.path.basename(agreement.document.name),
            'url': agreement.url
        })

    return render(request, 'superadmin/agreements.html', {'form': form, 'custom_agreements': custom_agreements})


@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def meetings_settings(request):
    if request.method == 'POST':
        form = MeetingsSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully")
            return redirect(reverse('superadmin_meetings_settings'))
        messages.error(request, form.errors)
    else:
        form = MeetingsSettingsForm(MeetingsSettingsForm.initial_values())

    return render(request, 'superadmin/meetings.html', {
        'form': form,
        'default_onlineafspraken_url': settings.ONLINE_MEETINGS_URL,
        'default_videocall_api_url': settings.VIDEO_CALL_RESERVE_ROOM_URL,
    })


class OptionalFeatures(SuperAdminView):
    http_method_names = ['post', 'get']

    def get_context(self, context):
        context.update({
            'profile_sets': ProfileSet.objects.all()
        })
        return context

    def post(self, request):
        form = OptionalFeaturesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/superadmin/optional_features')

        return render(request, 'superadmin/optional_features.html', self.get_context({
            'form': form,
        }))

    def get(self, request):
        return render(request, 'superadmin/optional_features.html', self.get_context({}))


@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def profileset_add(request):
    if request.method == 'POST':
        form = ProfileSetForm(request.POST)
        if form.is_valid():
            form.save(ProfileSet())
            return redirect('/superadmin/optional_features')
    else:
        form = ProfileSetForm(ProfileSetForm.initial_values(ProfileSet()))

    return render(request, 'superadmin/profile_set_form.html', {
        'title': "Create new profile-set",
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def profileset_edit(request, pk):
    profile_set = get_object_or_404(ProfileSet, pk=pk)
    if request.method == 'POST':
        form = ProfileSetForm(request.POST)
        if form.is_valid():
            form.save(profile_set)
            return redirect('/superadmin/optional_features')
    else:
        form = ProfileSetForm(ProfileSetForm.initial_values(profile_set))

    return render(request, 'superadmin/profile_set_form.html', {
        'title': "Update profile-set %s" % profile_set.name,
        'profile_set': profile_set,
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def profileset_delete(request, pk):
    profile_set = get_object_or_404(ProfileSet, pk=pk)
    if request.method == 'POST':
        if request.POST['confirmed'] == 'true':
            profile_set.delete()
            return redirect('/superadmin/optional_features')

    return render(request, 'superadmin/profile_set_delete_form.html', {
        'profile_set': profile_set,
    })

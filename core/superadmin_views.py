import json
import logging

from auditlog.models import LogEntry
from datetime import timedelta
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views import View
from django.utils import timezone
from celery.result import AsyncResult
from core.constances import OIDC_PROVIDER_OPTIONS
from core.models import Group
from core.tasks import replace_domain_links, elasticsearch_rebuild_for_tenant
from core.lib import tenant_schema, is_valid_domain
from core.superadmin.forms import AuditLogFilter, SettingsForm, ScanIncidentFilter
from control.tasks import get_db_disk_usage, get_file_disk_usage, copy_group_to_tenant
from file.models import ScanIncident
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
        db_usage = get_db_disk_usage(tenant_schema())
        file_usage = get_file_disk_usage(tenant_schema())

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
            'form': form
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
        logs = filtered_qs.qs[offset:offset+page_size+1] # grab one extra so we can check if there are more pages
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
            sites.append({ 'schema': client.schema_name, 'domain': client.get_primary_domain().domain })

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
            'sites':  sites,
            'items': items
        }

        return render(request, 'superadmin/group_copy.html', context)

    def post(self, request):
        try:
            assert request.POST.get("group"), "Provide group"
            assert request.POST.get("target_tenant"), "Provide target tenant"

            group_id = request.POST.get("group")
            target_tenant = request.POST.get("target_tenant")
            action_user_id = request.user.id
            copy_group_to_tenant.delay(tenant_schema(), action_user_id, group_id, target_tenant)
            messages.success(request, f"Copy group for {group_id} to {target_tenant} started.")

        except AssertionError as e:
            messages.error(request, f"Error: {e}")

        return redirect('/superadmin/group_copy')

@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def tasks(request):
    # pylint: disable=unused-argument
    current_domain = request.tenant.get_primary_domain().domain

    context = {}

    if request.POST:
        if request.POST.get("task", False) == "elasticsearch_rebuild":
            elasticsearch_rebuild_for_tenant.delay(tenant_schema())
            messages.success(request, 'Elasticsearch rebuild started')
        elif request.POST.get("task", False) == "replace_links":
            replace_domain = request.POST.get("replace_domain") if request.POST.get("replace_domain") else current_domain
            if not is_valid_domain(replace_domain):
                messages.error(request, f"The domain {replace_domain} is not a valid domain")
            elif current_domain == replace_domain:
                messages.error(request, "Please provide the domain name to replace")
            else:
                replace_domain_links.delay(tenant_schema(), replace_domain)
                messages.success(request, f"Replace links for {replace_domain} started.")
        else:
            messages.error(request, "Invalid command")

        return redirect('/superadmin/tasks')

    return render(request, 'superadmin/tasks.html', context)

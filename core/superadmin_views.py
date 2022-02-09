import json
import logging
from auditlog.models import LogEntry
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views import View
from core.constances import OIDC_PROVIDER_OPTIONS
from core.tasks import elasticsearch_rebuild, replace_domain_links
from core.lib import tenant_schema, is_valid_domain
from core.superadmin.forms import AuditLogFilter, SettingsForm, ScanIncidentFilter
from control.tasks import get_db_disk_usage, get_file_disk_usage
from file.models import ScanIncident

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

@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def tasks(request):
    # pylint: disable=unused-argument

    current_domain = request.tenant.get_primary_domain().domain
    context = {}

    if request.POST:
        if request.POST.get("task", False) == "elasticsearch_rebuild":
            elasticsearch_rebuild.delay(tenant_schema())
            messages.success(request, 'Elasticsearch rebuild started')
        elif request.POST.get("task", False) == "replace_links":
            replace_domain = request.POST.get("replace_domain") if request.POST.get("replace_domain") else current_domain
            replace_elgg_id = bool(request.POST.get("replace_elgg_id", False))
            if not is_valid_domain(replace_domain):
                messages.error(request, f"The domain {replace_domain} is not a valid domain")
            elif current_domain == replace_domain and not replace_elgg_id:
                messages.error(request, "Leaving the old domain empty only makes sense for replacing ELGG id's")
            else:
                replace_domain_links.delay(tenant_schema(), replace_domain, replace_elgg_id)
                messages.success(request, f"Replace links for {replace_domain} with replace ELGG id's = {replace_elgg_id} started.")

        else:
            messages.error(request, "Invalid command")

    return render(request, 'superadmin/tasks.html', context)

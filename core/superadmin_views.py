import logging
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views import View
from core.tasks import elasticsearch_rebuild, replace_domain_links
from core.lib import tenant_schema, is_valid_domain
from core.superadmin.forms import SettingsForm
from control.tasks import get_db_disk_usage, get_file_disk_usage

logger = logging.getLogger(__name__)


class Dashboard(LoginRequiredMixin, UserPassesTestMixin, View):
    http_method_names = ['get']

    def test_func(self):
        return self.request.user.is_superadmin

    def handle_no_permission(self):
        return redirect('/')

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

class Settings(LoginRequiredMixin, UserPassesTestMixin, View):
    http_method_names = ['post', 'get']

    def test_func(self):
        return self.request.user.is_superadmin

    def handle_no_permission(self):
        return redirect('/')

    def post(self, request):
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/superadmin/settings')

        return render(request, 'superadmin/settings.html', {'form': form})

    def get(self, request):
        context = {
        }

        return render(request, 'superadmin/settings.html', context)


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

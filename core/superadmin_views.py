import logging
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from core.tasks import elasticsearch_rebuild, replace_domain_links
from core.lib import tenant_schema, is_valid_domain

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(lambda u: u.is_superadmin, login_url='/', redirect_field_name=None)
def home(request):
    # pylint: disable=unused-argument

    context = {
    }

    return render(request, 'superadmin/home.html', context)

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
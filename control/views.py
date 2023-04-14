import logging
import os
import mimetypes
import csv

from django_tenants.utils import tenant_context, schema_context
from io import StringIO
from pip._internal.utils.filesystem import format_file_size
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages, auth
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import FileResponse, HttpResponseNotFound, StreamingHttpResponse
from django.shortcuts import render, redirect, reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from control.lib import get_full_url, schema_config
from core.lib import get_full_url as subsite_url
from control.utils.backup import schedule_backup
from tenants.models import Client, Agreement, AgreementVersion
from control.models import AccessLog, AccessCategory, SiteFilter, Task, ElasticsearchStatus
from control.forms import AddSiteForm, DeleteSiteForm, ConfirmSiteBackupForm, SearchUserForm, AgreementAddForm, AgreementAddVersionForm
from core.models import SiteStat
from user.models import User

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_superadmin


@login_required
@user_passes_test(is_admin)
def home(request):
    # pylint: disable=unused-argument

    context = {
        'name': settings.ENV,
        'site_count': Client.objects.exclude(schema_name='public').filter(is_active=True).count()
    }

    return render(request, 'home.html', context)


@login_required
@user_passes_test(is_admin)
def sites(request):
    # pylint: disable=unused-argument

    f = SiteFilter(
        request.GET,
        queryset=Client.objects.exclude(schema_name='public').all()
    )

    page = request.GET.get('page', 1)

    paginator = Paginator(f.qs, 50)
    try:
        sites = paginator.page(page)
    except PageNotAnInteger:
        sites = paginator.page(1)
    except EmptyPage:
        sites = paginator.page(paginator.num_pages)

    context = {
        'filter': f,
        'sites': sites,
    }

    return render(request, 'sites.html', context)


@login_required
@user_passes_test(is_admin)
def site(request, site_id):
    # pylint: disable=unused-argument

    site = Client.objects.get(id=site_id)

    with tenant_context(site):
        db_size_dates = list(SiteStat.objects.filter(stat_type='DB_SIZE').values_list('created_at', flat=True))[-50:]
        db_size_data = list(SiteStat.objects.filter(stat_type='DB_SIZE').values_list('value', flat=True))[-50:]
        db_stat_days = []
        for date in db_size_dates:
            db_stat_days.append(date.strftime("%d-%b-%Y"))

        disk_size_dates = list(SiteStat.objects.filter(stat_type='DISK_SIZE').values_list('created_at', flat=True))[-50:]
        disk_size_data = list(SiteStat.objects.filter(stat_type='DISK_SIZE').values_list('value', flat=True))[-50:]
        disk_stat_days = []
        for date in disk_size_dates:
            disk_stat_days.append(date.strftime("%d-%b-%Y"))

    context = {
        'site': site,
        'site_id': site_id,
        'site_name': schema_config(site.schema_name, 'NAME'),
        'db_stat_days': db_stat_days,
        'db_stat_data': db_size_data,
        'disk_stat_days': disk_stat_days,
        'disk_stat_data': disk_size_data
    }

    return render(request, 'site.html', context)


@login_required
@user_passes_test(is_admin)
def sites_add(request):
    # pylint: disable=unused-argument

    if request.method == 'POST':
        form = AddSiteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            schema_name = data.get("schema_name")
            domain = data.get("domain")
            backup = data.get("backup")

            if backup:
                task = Task.objects.create_task('control.tasks.restore_site', (backup, schema_name, domain))
            else:
                task = Task.objects.create_task('control.tasks.add_site', (schema_name, domain))

            messages.info(request, "Add site {%s} gestart in achtergrond (task.id=%s)" % (domain, task.id))

            return redirect(reverse('sites'))
    else:
        form = AddSiteForm(initial={})

    context = {
        'form': form
    }

    return render(request, 'sites_add.html', context)


@login_required
@user_passes_test(is_admin)
def tasks(request):
    # pylint: disable=unused-argument
    page = request.GET.get('page', 1)

    paginator = Paginator(Task.objects.all(), 50)
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)

    context = {
        'tasks': tasks,
    }

    return render(request, 'tasks.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "GET"])
def sites_delete(request, site_id):
    # pylint: disable=unused-argument
    site = Client.objects.get(id=site_id)

    if request.method == 'POST':
        form = DeleteSiteForm(request.POST)
        if form.is_valid():
            task = Task.objects.create_task('control.tasks.delete_site', (site.id,))

            messages.info(request, "Removed site %s gestart in achtergrond (task.id=%s)" % (site.primary_domain, task.id))

            return redirect(reverse('sites'))

    else:
        form = DeleteSiteForm(initial={
            'site_id': site.id
        })

    context = {
        'site': site,
        'form': form
    }

    return render(request, 'sites_delete.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "GET"])
def sites_disable(request, site_id):
    site = Client.objects.get(id=site_id)

    if request.method == 'POST':
        task = Task.objects.create_task('control.tasks.update_site', (site_id, {"is_active": False}))
        messages.info(request, "Disable site %s gestart in achtergrond (task.id=%s)" % (site.primary_domain, task.id))
        return redirect(reverse('sites'))

    context = {
        'site': site,
    }

    return render(request, 'sites_disable.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "GET"])
def sites_enable(request, site_id):
    site = Client.objects.get(id=site_id)

    if request.method == 'POST':
        task = Task.objects.create_task('control.tasks.update_site', (site_id, {"is_active": True}))
        messages.info(request, "Enable site %s gestart in achtergrond (task.id=%s)" % (site.primary_domain, task.id))
        return redirect(reverse('sites'))

    context = {
        'site': site,
    }

    return render(request, 'sites_enable.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "GET"])
def sites_backup(request, site_id):
    # pylint: disable=unused-argument
    site = Client.objects.get(id=site_id)
    actor = auth.get_user(request)

    if request.method == 'POST':
        form = ConfirmSiteBackupForm(request.POST)
        if form.is_valid():
            task = schedule_backup(site,
                                   actor,
                                   form.cleaned_data['include_files'],
                                   form.cleaned_data['create_archive'])

            context = {
                "site_name": schema_config(site.schema_name, 'NAME'),
                "task_id": str(task.id),
            }

            messages.info(request,
                          _("Backup site %(site_name)s is scheduled. The backup will soon be added to the list of backups below. Reference: %(task_id)s") % context)
            return redirect(reverse('site_backup', args=(site_id,)))

    else:
        form = ConfirmSiteBackupForm()

    context = {
        'site_id': site_id,
        'site_name': schema_config(site.schema_name, 'NAME'),
        'form': form,
        'access_logs': AccessLog.objects.filter(site=site),
        'backups': [{
            'created_at': log.created_at,
            'download': log.item_id.endswith('.zip'),
            'author': log.user.name,
            'download_url': get_full_url(reverse('download_backup', args=[site.id, log.item_id])),
            'filesize': format_file_size(os.path.join(settings.BACKUP_PATH, log.item_id)),
            'filename': log.item_id,
        } for log in AccessLog.objects.filter(
            type=AccessLog.AccessTypes.CREATE,
            category=AccessLog.custom_category(AccessCategory.SITE_BACKUP, site_id),
        )[:5]],
    }

    return render(request, 'sites_backup.html', context)


@login_required
@user_passes_test(is_admin)
def download_backup(request, site_id, backup_name):
    try:
        site = Client.objects.get(id=site_id)

        assert backup_name.endswith(f"_{site.schema_name}.zip"), "Invalid backup file name"

        filepath = os.path.join(settings.BACKUP_PATH, backup_name)
        if not os.path.isfile(filepath):
            return HttpResponseNotFound()

        AccessLog.objects.create(
            type=AccessLog.AccessTypes.DOWNLOAD,
            category=AccessLog.custom_category(AccessCategory.SITE_BACKUP, site_id),
            user=auth.get_user(request),
            item_id=backup_name,
            site=site,
        )

        chunk_size = 8192
        response = FileResponse(
            FileWrapper(open(filepath, 'rb'), chunk_size),
            content_type=mimetypes.guess_type(filepath)[0]
        )
        response['Content-Length'] = os.path.getsize(filepath)
        response['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(filepath)

        return response
    except Client.DoesNotExist:
        return HttpResponseNotFound("Client does not exist")
    except AssertionError as e:
        return HttpResponseNotFound(e)


@login_required
@user_passes_test(is_admin)
def tools(request):
    return render(request, 'tools.html')


@login_required
@user_passes_test(is_admin)
def download_site_admins(request):
    clients = Client.objects.exclude(schema_name='public', is_active=True)

    admins = []
    for client in clients:

        with tenant_context(client):

            users = User.objects.filter(roles__contains=['ADMIN'], is_active=True)
            for user in users:
                admins.append({
                    'name': user.name,
                    'email': user.email,
                    'client_id': client.id,
                    'client_domain': client.get_primary_domain().domain
                })

    def stream():
        buffer = StringIO()
        writer = csv.writer(buffer, delimiter=';', quotechar='"')
        writer.writerow(['name', 'email', 'site'])
        yield buffer.getvalue()

        for admin in admins:
            buffer = StringIO()
            writer = csv.writer(buffer, delimiter=';', quotechar='"')
            writer.writerow([admin['name'], admin['email'], admin['client_domain']])
            yield buffer.getvalue()

    response = StreamingHttpResponse(stream(), content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="site_admins.csv"'

    return response


@login_required
@user_passes_test(is_admin)
def search_user(request):
    if request.method == 'POST':
        form = SearchUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            email = data.get("email")
            clients = Client.objects.exclude(schema_name='public')
            data = []
            for client in clients:
                with tenant_context(client):
                    user = User.objects.filter(email=email, is_active=True).first()
                    if user:
                        data.append({
                            'user_name': user.name,
                            'user_email': user.email,
                            'user_external_id': user.external_id,
                            'id': client.id,
                            'schema': client.schema_name,
                            'domain': client.get_primary_domain().domain
                        })

            context = {
                'form': form,
                'sites': data,
            }

            return render(request, 'search_user.html', context)

    else:
        form = SearchUserForm(initial={})

    context = {
        'form': form
    }

    return render(request, 'search_user.html', context)


@login_required
@user_passes_test(is_admin)
def agreements(request, cluster_id=None):
    # pylint: disable=unused-argument

    context = {
        'agreements': Agreement.objects.all()
    }

    return render(request, 'agreements.html', context)


@login_required
@user_passes_test(is_admin)
def agreements_add(request):
    if request.method == 'POST':
        form = AgreementAddForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            name = data.get("name")
            Agreement.objects.create(name=name, description='')

            messages.info(request, f"Added agreement {name}")

            return redirect('/agreements')
    else:
        form = AgreementAddForm(initial={})

    context = {
        'form': form
    }

    return render(request, 'agreements_add.html', context)


@login_required
@user_passes_test(is_admin)
def agreements_add_version(request, agreement_id):
    if not Agreement.objects.filter(id=agreement_id).exists():
        return HttpResponseNotFound("Agreement not found")

    if request.method == 'POST':
        form = AgreementAddVersionForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data

            version = data.get("version")
            agreement_id = data.get("agreement_id")
            uploaded_file = request.FILES['document']

            agreement = Agreement.objects.get(id=agreement_id)
            version = AgreementVersion.objects.create(
                agreement=agreement,
                version=version,
                document=uploaded_file
            )

            messages.info(request, "Added version %s to agreement %s" % (version.version, agreement.name))

            return redirect('/agreements')
    else:
        form = AgreementAddVersionForm(initial={
            'agreement_id': agreement_id
        })

    context = {
        'form': form
    }

    return render(request, 'agreements_add.html', context)


@login_required
@user_passes_test(is_admin)
def elasticsearch_status(request):
    clients = Client.objects.exclude(schema_name='public')
    rows = []
    for client in clients:
        last_record = ElasticsearchStatus.objects.order_by('-created_at').filter(client=client).first()
        status = {}
        with schema_context(client.schema_name):
            from core import config
            status['name'] = config.NAME
            status['url'] = subsite_url("/login") + '?next=/superadmin/tasks'

        if last_record:
            status["created_at"] = last_record.created_at
            status["index_status"] = last_record.index_status_summary()
            status["access_status"] = last_record.access_status_summary()
            status['details_url'] = reverse("elasticsearch_status", args=[client.id])
        rows.append(status)

    # render summary of all sites with elasticsearch issues
    return render(request, "tools/elasticsearch_summary.html", {
        'rows': rows
    })


@login_required
@user_passes_test(is_admin)
def elasticsearch_status_details(request, client_id, record_id=None):
    client = Client.objects.get(id=client_id)
    if not record_id:
        record = ElasticsearchStatus.objects.filter(client=client).first()
    else:
        record = ElasticsearchStatus.objects.get(client=client,
                                                 id=record_id)
    if not record:
        return HttpResponseNotFound("Invalid parameters")

    with schema_context(client.schema_name):
        from core import config
        site_name = config.NAME
        site_url = subsite_url("/login") + '?next=/superadmin/tasks'

    context = {
        'record': record,
        'site_name': site_name,
        'site_url': site_url,
        'previous': ElasticsearchStatus.objects.previous(record.client, record.created_at),
        'next': ElasticsearchStatus.objects.next(record.client, record.created_at),
    }

    # render elasticsearch status of one site
    return render(request, "tools/elasticsearch_details.html", context)

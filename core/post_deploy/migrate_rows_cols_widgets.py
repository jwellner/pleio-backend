import traceback

from celery.utils.log import get_task_logger

from cms.models import Page
from core.lib import is_schema_public, tenant_schema
from post_deploy import post_deploy_action

from core.models import Group

logger = get_task_logger(__name__)


@post_deploy_action(auto=False)
def deploy_action():
    if is_schema_public():
        return

    for page in Page.objects.filter(page_type='campagne'):
        do_migrate_campagne_page_rows(page)
    for group in Group.objects.all():
        do_migrate_group_widgets(group)
        do_migrate_group_link_lists(group)


def do_migrate_group_widgets(group: Group):
    try:
        if group.widget_repository:
            return

        group.widget_repository = []
        for widget in group.widgets.order_by('position'):
            group.widget_repository.append({
                'type': widget.type,
                'settings': [{
                    'key': s.get('key'),
                    'value': s.get('value'),
                    'richDescription': s.get('richDescription'),
                    'attachmentId': s.get('attachment')
                } for s in widget.settings]
            })
        group.save()
    except Exception as e:
        logger.error("%s: %s", str(e.__class__), str(e))
        logger.error("do_migrate_group_widgets @ %s %s", tenant_schema(), traceback.format_exc())


def do_migrate_campagne_page_rows(page: Page):
    try:
        if page.row_repository:
            return

        page.row_repository = []
        for row in page.rows.order_by('position'):
            page.row_repository.append({
                "isFullWidth": row.is_full_width,
                "columns": [{
                    "width": c.width,
                    "widgets": [{
                        'type': w.type,
                        'settings': [{
                            'key': s.get('key'),
                            'value': s.get('value'),
                            'richDescription': s.get('richDescription'),
                            'attachmentId': s.get('attachment'),
                        } for s in w.settings]
                    } for w in c.widgets.order_by('position')]
                } for c in row.columns.order_by('position')]
            })
        page.save()
    except Exception as e:
        logger.error("%s: %s", str(e.__class__), str(e))
        logger.error("do_migrate_campagne_page_rows @ %s %s", tenant_schema(), traceback.format_exc())


def do_migrate_group_link_lists(group: Group):
    widgets = []
    changed = False

    for widget in group.widget_repository:
        if widget['type'] == 'linklist':
            widget['type'] = 'linkList'
            changed = True
        widgets.append(widget)

    if changed:
        group.widget_repository = widgets
        group.save()

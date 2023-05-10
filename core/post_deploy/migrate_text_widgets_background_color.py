from post_deploy import post_deploy_action

from cms.models import Page
from core.lib import is_schema_public


def _add_background_color_to_text_widgets(widget):
    if widget['type'] == 'text':
        for setting in widget.get('settings', []):
            if setting['key'] == 'backgroundColor':
                return widget
        widget['settings'].append({
            "key": "backgroundColor",
            "value": "white",
            "attachmentId": None,
            "richDescription": None
        })
    return widget


@post_deploy_action(auto=True)
def task():
    if is_schema_public():
        return

    for page in Page.objects.filter_campagne():
        page.update_widgets(callback=_add_background_color_to_text_widgets)
        page.save()

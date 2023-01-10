from django.utils.translation import gettext_lazy as _


def get_activity_filters():
    yield {
        "key": "statusupdate",
        "value": _("Update"),
    }

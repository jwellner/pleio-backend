from django.utils.translation import gettext_lazy as _


def get_search_filters():
    yield {
        "key": "user",
        "value": _("User"),
        "plural": _("Users"),
    }

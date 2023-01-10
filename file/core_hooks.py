from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "file",
        "value": _("File"),
    }


def get_search_filters():
    yield {
        "key": "file",
        "value": _("File"),
        "plural": _("Files"),
    }
    yield {
        "key": "folder",
        "value": _("Folder"),
        "plural": _("Folders"),
    }

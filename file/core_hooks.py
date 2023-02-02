from django.utils.translation import gettext_lazy as _

from core.exceptions import IgnoreIndexError, ExceptionDuringQueryIndex
from core.tests.helpers import GraphQLClient
from user.models import User


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


def test_elasticsearch_index(index_name):
    if index_name != 'file':
        raise IgnoreIndexError()

    try:
        client = GraphQLClient()
        client.force_login(User.objects.filter(is_superadmin=True).first())
        client.post("""
        query ElasticsearchQuery($type: String) {
            search(subtype: $type, subtypes: [$type]) {
                total
                totals {
                    title
                    subtype
                    total
                }
                edges {
                    guid
                    ... on File {
                        title
                    }
                    ... on Folder {
                        title
                    }
                    ... on Pad {
                        title
                    }
                }
            }
        }
        """, {
            'type': 'file',
        })
    except Exception as e:
        raise ExceptionDuringQueryIndex(str(e))

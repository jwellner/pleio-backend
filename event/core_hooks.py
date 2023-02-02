from django.utils.translation import gettext_lazy as _

from core.exceptions import ExceptionDuringQueryIndex, IgnoreIndexError
from core.tests.helpers import GraphQLClient
from user.models import User


def get_entity_filters():
    yield {
        "key": "event",
        "value": _("Event"),
    }


def get_activity_filters():
    yield {
        "key": "event",
        "value": _("Event"),
    }


def get_search_filters():
    yield {
        "key": "event",
        "value": _("Event"),
        "plural": _("Events"),
    }


def test_elasticsearch_index(index_name):
    if index_name != 'event':
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
                    ... on Event {
                        title
                    }
                }
            }
        }
        """, {
            'type': 'event',
        })
    except Exception as e:
        raise ExceptionDuringQueryIndex(str(e))

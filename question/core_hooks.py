from django.utils.translation import gettext_lazy as _

from core.exceptions import ExceptionDuringQueryIndex, IgnoreIndexError
from core.tests.helpers import GraphQLClient
from user.models import User


def get_entity_filters():
    yield {
        "key": "question",
        "value": _("Question"),
    }


def get_activity_filters():
    yield {
        "key": "question",
        "value": _("Question"),
    }


def get_search_filters():
    yield {
        "key": "question",
        "value": _("Question"),
        "plural": _("Questions"),
    }


def test_elasticsearch_index(index_name):
    if index_name != 'question':
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
                    ... on Question {
                        title
                    }
                }
            }
        }
        """, {
            'type': 'question',
        })
    except Exception as e:
        raise ExceptionDuringQueryIndex(str(e))

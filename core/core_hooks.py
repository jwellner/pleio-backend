from django.utils.translation import gettext_lazy as _

from core.exceptions import IgnoreIndexError, ExceptionDuringQueryIndex
from core.tests.helpers import GraphQLClient
from user.models import User


def get_search_filters():
    yield {
        "key": "group",
        "value": _("Group"),
        "plural": _("Groups"),
    }


def test_elasticsearch_index(index_name):
    if index_name == 'group':
        _test_group_query()
        return

    if index_name == 'user':
        _test_user_query()
        return

    raise IgnoreIndexError()


def _test_group_query():
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
                    ... on Group {
                        name
                    }
                }
            }
        }
        """, {
            'type': 'group',
        })
    except Exception as e:
        raise ExceptionDuringQueryIndex(str(e))


def _test_user_query():
    try:
        client = GraphQLClient()
        client.force_login(User.objects.filter(is_superadmin=True).first())
        client.post("""
        query ElasticsearchQuery($q: String!) {
            users(q: $q) {
                total
                filterCount {
                    name
                    values {
                        key
                        count
                    }
                }
                fieldsInOverview {
                    key
                    label
                }
                edges {
                    guid
                    name
                    email
                }
            }
        }
        """, {
            'q': '',
        })
    except Exception as e:
        raise ExceptionDuringQueryIndex(str(e))

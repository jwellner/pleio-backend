from core.lib import get_acl
from user.models import User
from core.models import ProfileField
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path


def resolve_users(_, info, q="", filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    ids = []

    user = info.context["request"].user
    tenant_name = parse_tenant_config_path("")

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if q:
        s = Search(index='user').query(
            Q('query_string', query=q, fields=['name', 'email']) |
            Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
                    Q('match', _profile__user_profile_fields__value=q) &
                    Q('terms', _profile__user_profile_fields__read_access=list(get_acl(user)))
                    ]
                )
            )
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        ).filter(
            'term', is_active=True
        )

    else:
        s = Search(index='user').filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        ).filter(
            'term', is_active=True
        )

    if filters:
        for f in filters:
            s = s.filter(
                Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
                        Q('match', _profile__user_profile_fields__key=f['name']) &
                        Q('terms', _profile__user_profile_fields__value=f['values'])
                        ]
                    )
                )
            )

    response = s.execute()

    for hit in response:
        ids.append(hit['id'])

    users = User.objects.filter(id__in=ids)
    edges = users[offset:offset+limit]

    fields_in_overview = []
    for item in ProfileField.objects.filter(is_in_overview=True).all():
        fields_in_overview.append({ 'key': item.key, 'label': item.name })

    return {
        'total': users.count(),
        'edges': edges,
        'filterCount': [],
        'fieldsInOverview': fields_in_overview
    }

from core.lib import get_acl
from user.models import User
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path


def resolve_users(_, info, q="", filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    ids = []

    user = info.context.user
    tenant_name = parse_tenant_config_path("")

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if q:
        s = Search(index='users').query(
            Q('multi_match', query=q, fields=['name^2', ]) |
            Q('nested', path='_profile', query=Q('bool', must=[
                    Q('match', _profile__user_profile_fields__value=q) &
                    Q('terms', _profile__user_profile_fields__read_access=list(get_acl(user)))
                    ]
                )
            )
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        )

    else:
        s = Search(index='users').filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        )

    if filters:
        for f in filters:
            s = s.filter(
                Q('nested', path='_profile', query=Q('bool', must=[
                        Q('match', _profile__user_profile_fields__key=f['name']) &
                        Q('terms', _profile__user_profile_fields__value=f['values'])
                        ]
                    )
                )
            )

    response = s.execute()

    for hit in response:
        ids.append(hit['id'])

    users = User.objects.filter(id__in=ids, is_active=True)
    edges = users[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': edges,
        'filterCount': []
    }

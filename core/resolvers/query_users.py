from core.models import User
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError


def resolve_users(_, info, q=None, filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if q:
        s = Search().query(Q('multi_match', query=q, fields=['name^2', 'email'])).filter('terms', type=['user'])[offset:offset+limit]
        response = s.execute()
        ids = []
        for hit in response:
            ids.append(hit['id'])
        users = User.objects.filter(id__in=ids)[offset:offset+limit]
    else:
        users = User.objects.all()[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': users,
        'filterCount': None
    }

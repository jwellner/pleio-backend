from core.lib import get_acl
from core import config
from core.models import ProfileField
from user.models import User
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path


def resolve_users(_, info, q="", filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches

    user = info.context["request"].user
    tenant_name = parse_tenant_config_path("")

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if q:
        s = Search(index='user').query(
            Q('simple_query_string', query=q, fields=[
                'name^3',
                'email',
            ])
            | Q('bool', must=[
                Q('simple_query_string', query=q, fields=['profile.user_profile_fields.value']),
                Q('terms', profile__user_profile_fields__read_access=list(get_acl(user)))])
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'term', tenant_name=tenant_name
        ).filter(
            'term', is_active=True
        )
    else:
        s = Search(index='user').filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'term', tenant_name=tenant_name
        ).filter(
            'term', is_active=True
        )

    if filters:
        for f in filters:
            s = s.filter(
                Q('bool', must=[
                    Q('match', profile__user_profile_fields__key=f['name']) & (
                            Q('terms', profile__user_profile_fields__value__raw=f['values']) |
                            Q('terms', profile__user_profile_fields__value_list=f['values'])
                    )])
            )

    total = s.count()

    # Sort on name is score is equal
    s = s.sort(
        '_score',
        {'name.raw': {'order': 'asc'}}
    )

    s = s[offset:offset + limit]
    response = s.execute()

    ids = []
    for hit in response:
        ids.append(hit['id'])

    objects = User.objects.filter(id__in=ids)

    # use elasticsearch ordering on objects
    id_dict = {str(d.id): d for d in objects}
    sorted_objects = [id_dict[id] for id in ids]

    fields_in_overview = []

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    for item in ProfileField.objects.filter(is_in_overview=True, id__in=profile_section_guids):
        fields_in_overview.append({ 'key': item.key, 'label': item.name })

    return {
        'total': total,
        'edges': sorted_objects,
        'filterCount': [],
        'fieldsInOverview': fields_in_overview
    }

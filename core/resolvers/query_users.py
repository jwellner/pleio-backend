from core.lib import get_acl
from core import config, constances
from core.models import ProfileField
from core.resolvers import shared
from user.models import User
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path


def resolve_users(_, info, q="", filters=None, offset=0, limit=20, profileSetGuid=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches

    user = info.context["request"].user
    tenant_name = parse_tenant_config_path("")

    shared.assert_authenticated(user)
    if profileSetGuid:
        shared.assert_is_profile_set_manager(user, profileSetGuid)

    if q:
        s = Search(index='user').query(
            Q('simple_query_string', query=q, fields=['name^3', 'email']) |
            Q('nested', path='user_profile_fields', query=Q('bool', must=[
                Q('match', user_profile_fields__value=q),
                Q('terms', user_profile_fields__read_access=list(get_acl(user)))
            ]))
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

    if profileSetGuid:
        profile_set = user.profile_sets.filter(pk=profileSetGuid).first()

        user_profile_field = user.profile.user_profile_fields.filter(profile_field__key=profile_set.field.key).first()
        if not user_profile_field or not user_profile_field.value:
            raise GraphQLError(constances.MISSING_REQUIRED_FIELD % profile_set.field.key)

        if user_profile_field.value_list_field_indexing:
            set_filter = Q('terms', user_profile_fields__value_list=user_profile_field.value_list_field_indexing)
        else:
            set_filter = Q('terms', user_profile_fields__value__raw=[user_profile_field.value_field_indexing])

        s = s.filter(
            Q('nested', path='user_profile_fields', query=Q('bool', must=[
                Q('match', user_profile_fields__key=profile_set.field.key) & set_filter
            ]))
        )

    if filters:
        for f in filters:
            s = s.filter(
                Q('nested', path='user_profile_fields', query=Q('bool', must=[
                    Q('match', user_profile_fields__key=f['name']) & (
                            Q('terms', user_profile_fields__value__raw=f['values']) |
                            Q('terms', user_profile_fields__value_list=f['values'])
                    )])
                  )
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
        fields_in_overview.append({'key': item.key, 'label': item.name})

    return {
        'total': total,
        'edges': sorted_objects,
        'filterCount': [],
        'fieldsInOverview': fields_in_overview
    }

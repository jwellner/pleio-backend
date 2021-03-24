from core import config
from core.lib import get_acl
from core.models import ProfileField
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search, Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path

def get_filter_options(key, user):
    options = []

    tenant_name = parse_tenant_config_path("")

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    user_acl = list(get_acl(user))

    s = Search(index='user').query(
        Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
                Q('terms', _profile__user_profile_fields__read_access=user_acl)
                ]
            )
        )
    ).filter(
        'term', tenant_name=tenant_name
    ).exclude(
        'term', is_active=False
    )

    # TODO: use aggregations
    for hit in s.scan():
        for field in hit['_profile']['user_profile_fields']:
            if field['key'] == key and not set(user_acl).isdisjoint(set(field['read_access'])):
                options.append(field['value'])

    return sorted(list(set(options)))


def resolve_filters(_, info):
    # pylint: disable=unused-argument
    user_filters = []

    user = info.context["request"].user

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    profile_fields = ProfileField.objects.filter(id__in=profile_section_guids)

    for field in profile_fields:
        if field.is_filter and field.is_filterable:
            if field.field_type in ['multi_select_field', 'select_field']:
                options = field.field_options
            else:
                options = get_filter_options(field.key, user)
            if options:
                user_filters.append({
                    "name": field.key,
                    "fieldType": field.field_type,
                    "label": field.name,
                    "keys": options
                })

    return {
        'users': user_filters
    }

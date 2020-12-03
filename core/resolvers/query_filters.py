from core import config
from core.lib import get_acl
from core.models import ProfileField
from core.constances import NOT_LOGGED_IN
from elasticsearch_dsl import Search
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path

def get_filter_options(key, user):
    options = []

    tenant_name = parse_tenant_config_path("")

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    s = Search(index='user').filter(
        'terms', read_access=list(get_acl(user))
    ).filter(
        'match', tenant_name=tenant_name
    )

    response = s.execute()
    for hit in response:
        for field in hit['_profile']['user_profile_fields']:
            if field['key'] == key:
                options.append(field['value'])

    return list(set(options))


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

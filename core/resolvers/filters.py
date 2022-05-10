from ariadne import ObjectType
from core import config
from core.lib import get_acl
from core.models import ProfileField, Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from elasticsearch_dsl import Search, Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path

filters = ObjectType("Filters")


def get_filter_options(key, user, group=None):
    options = []

    tenant_name = parse_tenant_config_path("")

    user_acl = list(get_acl(user))

    s = Search(index='user').filter(
        Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
            Q('terms', _profile__user_profile_fields__read_access=user_acl)
        ]))
    ).filter(
        'term', tenant_name=tenant_name
    ).exclude(
        'term', is_active=False
    )

    if group is not None:
        s = s.filter(
            Q('nested', path='memberships', query=Q('bool', must=[
                Q('match', memberships__group_id=group.id)
            ], must_not=[
                Q('match', memberships__type="pending")
            ]))
        )

    for hit in s.scan():
        for field in hit['_profile']['user_profile_fields']:
            if field['key'] == key and not set(user_acl).isdisjoint(set(field['read_access'])):
                if field['value_list']:
                    options.extend(field['value_list'])
                elif field['value'] not in [None, '']:
                    options.append(field['value'])

    return sorted(list(set(options)), key=str.lower)


@filters.field("users")
def resolve_users_filters(_, info, groupGuid=None):
    # pylint: disable=unused-argument
    user_filters = []

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if groupGuid:
        try:
            group = Group.objects.get(id=groupGuid)
        except Group.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    profile_fields = ProfileField.objects.filter(id__in=profile_section_guids)

    for field in profile_fields:
        if group:
            is_filter = group.profile_field_settings.filter(show_field=True, profile_field=field).exists()
        else:
            is_filter = field.is_filter

        if is_filter and field.is_filterable:
            if not group and field.field_type in ['multi_select_field', 'select_field']:
                options = field.field_options
            else:
                options = get_filter_options(field.key, user, group)
            if options:
                user_filters.append({
                    "name": field.key,
                    "fieldType": field.field_type,
                    "label": field.name,
                    "keys": options
                })

    return user_filters

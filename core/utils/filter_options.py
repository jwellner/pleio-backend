from django_tenants.utils import parse_tenant_config_path
from elasticsearch_dsl import Search, Q

from core.lib import get_acl


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

    # TODO: use aggregations
    for hit in s.scan():
        for field in hit['_profile']['user_profile_fields']:
            if field['key'] == key and not set(user_acl).isdisjoint(set(field['read_access'])):
                options.append(field['value'])

    return sorted(list(set(options)), key=str.lower)

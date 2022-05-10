from core.lib import get_acl
from core import config
from core.models import ProfileField, Group, GroupMembership
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError
from django_tenants.utils import parse_tenant_config_path


def resolve_members(_, info, groupGuid, q="", filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    try:
        user = info.context["request"].user
        tenant_name = parse_tenant_config_path("")

        if not user.is_authenticated:
            raise GraphQLError(NOT_LOGGED_IN)

        group = Group.objects.get(id=groupGuid)

        query = Search(index='user').filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'term', tenant_name=tenant_name
        ).filter(
            'term', is_active=True
        ).filter(
            Q('nested', path='memberships', query=Q('bool', must=[
                Q('match', memberships__group_id=group.guid)
            ], must_not=[
                Q('match', memberships__type="pending")
            ]))
        )

        if q:
            query = query.filter(
                Q('simple_query_string', query=q, fields=['name^3', 'email']) |
                Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
                    Q('match', _profile__user_profile_fields__value=q),
                    Q('terms', _profile__user_profile_fields__read_access=list(get_acl(user)))
                ]))
            )

        if filters:
            for f in filters:
                query = query.filter(
                    Q('nested', path='_profile.user_profile_fields', query=Q('bool', must=[
                        Q('match', _profile__user_profile_fields__key=f['name']) & (
                                Q('terms', _profile__user_profile_fields__value__raw=f['values']) |
                                Q('terms', _profile__user_profile_fields__value_list=f['values'])
                        )])
                      )
                )

        total = query.count()

        # Sort on name is score is equal
        query = query.sort(
            {'memberships.admin_weight': {'order': 'asc',
                                          'nested': {'path': 'memberships'}}},
            '_score',
            {'name.raw': {'order': 'asc'}},
        )

        query = query[offset:offset + limit]
        response = query.execute()

        ids = []
        for hit in response:
            ids.append(hit['id'])

        objects = GroupMembership.objects.filter(user__id__in=ids, group__id=groupGuid)

        # use elasticsearch ordering on objects
        id_dict = {str(d.user.id): d for d in objects}
        sorted_objects = [id_dict.get(id) for id in ids]

        fields_in_overview = []

        for item in group.profile_field_settings.filter(show_field=True):
            fields_in_overview.append({'key': item.profile_field.key,
                                       'label': item.profile_field.name})

        return {
            'total': total,
            'edges': sorted_objects,
            'fieldsInOverview': fields_in_overview
        }
    except Group.DoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

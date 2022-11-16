from core.models import Group, GroupMembership, UserProfileField
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from django.db.models import Q
from graphql import GraphQLError

from core.resolvers import shared


def resolve_members(_, info, groupGuid, q="", filters=None, offset=0, limit=20):
    try:
        user = info.context["request"].user

        if not user.is_authenticated:
            raise GraphQLError(NOT_LOGGED_IN)

        group = Group.objects.get(id=groupGuid)
        shared.assert_group_member(user, group)

        query = GroupMembership.objects.filter(group_id=groupGuid,
                                               user__is_superadmin=False).exclude(type='pending')

        if q:
            user_matches = Q(user__name__icontains=q) | Q(user__email__icontains=q)

            fields_in_overview = list_fields_in_overview(group)
            query_profile = UserProfileField.objects.visible(user).filter(
                profile_field__key__in=[f['key'] for f in fields_in_overview],
                value__icontains=q).values_list('user_profile__user_id', flat=True)
            profile_field_matches = Q(user_id__in=query_profile)

            # pylint: disable=unsupported-binary-operation
            query = query.filter(user_matches | profile_field_matches)

        if filters:
            for f in filters:
                values_match: Q = None
                for value in f['values']:
                    value_match = Q(value=value)
                    value_match |= Q(value__startswith=value + ',')
                    value_match |= Q(value__contains=',' + value + ',')
                    value_match |= Q(value__endswith=',' + value)
                    if values_match:
                        values_match |= value_match
                    else:
                        values_match = value_match
                query = query.filter(user_id__in=UserProfileField.objects.filter(Q(profile_field__key=f['name']) & values_match).values_list('user_profile__user_id', flat=True))

        total = query.count()

        return {
            'total': total,
            'edges': query.order_by('admin_weight', 'user__name')[offset:offset + limit],
            'fieldsInOverview': list_fields_in_overview(group)
        }
    except Group.DoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)


def list_fields_in_overview(group):
    fields_in_overview = []
    for item in group.profile_field_settings.filter(show_field=True):
        fields_in_overview.append({'key': item.profile_field.key,
                                   'label': item.profile_field.name})
    return fields_in_overview

import logging
from datetime import timedelta
from user.models import User
from core.models import ProfileField, UserProfileField
from core.constances import INVALID_KEY
from graphql import GraphQLError
from django.db.models import Q, Case, When, Value
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

logger = logging.getLogger(__name__)

def resolve_users_by_birth_date(_, info, profileFieldGuid, futureDays=30, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals

    user = info.context["request"].user

    try:
        profile_field = ProfileField.objects.get(id=profileFieldGuid)
    except ObjectDoesNotExist:
        raise GraphQLError(INVALID_KEY)

    if not profile_field.field_type == "date_field":
        raise GraphQLError(INVALID_KEY)

    day = timezone.now() - timedelta(days=2)
    end_day = timezone.now() + timedelta(days=futureDays)

    filter_dates = Q()
    while day < end_day:
        filter_dates.add(
            Q(
                value_date__month=day.month,
                value_date__day=day.day
            ),
            Q.OR
        )
        day += timedelta(days=1)

    user_profile_fields = UserProfileField.objects.visible(user).filter(
        Q(profile_field=profile_field) &
        filter_dates
    ).order_by(
        Case(
            When(value_date__month__gte=day.month, then=Value(0)),
            When(value_date__month__lt=day.month, then=Value(1)),
        ),
        'value_date__month',
        'value_date__day',
    )

    ids = []
    selection = user_profile_fields[offset:offset+limit]
    for item in selection:
        ids.append(item.user_profile.user.guid)

    users = User.objects.filter(id__in=ids)

    # use birthday ordering on objects
    id_dict = {d.guid: d for d in users}
    sorted_users = [id_dict[id] for id in ids]

    return {
        'total': user_profile_fields.count(),
        'edges': sorted_users
    }

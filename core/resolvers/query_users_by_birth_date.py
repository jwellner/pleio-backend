import logging
from datetime import timedelta
from user.models import User
from core.constances import INVALID_KEY
from core.exceptions import InvalidFieldException
from graphql import GraphQLError
from django.utils import timezone

logger = logging.getLogger(__name__)

def resolve_users_by_birth_date(_, info, profileFieldGuid, futureDays=30, offset=0, limit=20):
    user = info.context["request"].user

    start_day = timezone.now() - timedelta(days=2)
    end_day = timezone.now() + timedelta(days=futureDays)

    try:
        sorted_users = User.objects.get_upcoming_birthday_users(profileFieldGuid, user, start_day, end_day, offset, limit)
    except InvalidFieldException:
        raise GraphQLError(INVALID_KEY)

    return {
        'total': len(sorted_users),
        'edges': sorted_users
    }

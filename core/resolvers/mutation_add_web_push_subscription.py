from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core import config
from core.models import Group, Widget, WebPushSubscription
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, COULD_NOT_ADD
from core.lib import clean_graphql_input


def resolve_add_web_push_subscription(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not config.PUSH_NOTIFICATIONS_ENABLED:
        raise GraphQLError(COULD_NOT_ADD)

    WebPushSubscription.objects.create(
        browser = clean_input.get("browser"),
        endpoint = clean_input.get("endpoint"),
        auth = clean_input.get("auth"),
        p256dh = clean_input.get("p256dh"),
        user = user
    )

    return {
        "success": True
    }

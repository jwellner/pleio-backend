from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group, Widget
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict

def resolve_add_group_widget(_, info, input):
    # pylint: disable=redefined-builtin
    settings = []
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("groupGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'settings' in clean_input:
        settings = clean_input.get("settings")

    widget = Widget.objects.create(
        group=group,
        position=clean_input.get("position"),
        type=clean_input.get("type"),
        settings=settings
    )

    return {
        "entity": widget
    }

import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Widget
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict
from cms.models import Page
from cms.utils import reorder_positions


def resolve_add_widget(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        page = Page.objects.get(id=clean_input.get("containerGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
        old_position = None
        new_position = clean_input.get("position")
        widget = Widget()

        widget.page = page

        widget.position = clean_input.get("position")
        widget.parent_id = clean_input.get("parentGuid")

        if clean_input.get("settings"):
            widget.settings = clean_input.get("settings")

        widget.type = clean_input.get("type")

        widget.save()

        reversion.set_user(user)
        reversion.set_comment("addWidget mutation")

        reorder_positions(widget, old_position, new_position)

    return {
        "widget": widget
    }
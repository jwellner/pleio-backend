from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import COULD_NOT_FIND
from core.models import Widget, Attachment
from cms.models import Column
from cms.utils import reorder_positions
from core.resolvers import shared


def resolve_edit_widget(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        widget = Widget.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(widget.page, user)

    old_position = update_position(widget, clean_input)
    update_column(widget, clean_input)
    update_settings(widget, clean_input, user)

    widget.save()

    reorder_positions(widget, old_position, clean_input.get("position"))

    return {
        "widget": widget
    }


def update_position(widget, clean_input):
    old_position = widget.position
    if 'position' in clean_input:
        widget.position = clean_input.get("position")
    return old_position


def update_column(widget, clean_input):
    if 'parentGuid' in clean_input:
        try:
            widget.column = Column.objects.get(id=clean_input.get("parentGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)


def update_settings(widget, clean_input, user):
    update_settings = []
    for setting in clean_input.get('settings', []):
        if setting.get("attachment"):
            attachment = Attachment.objects.create(upload=setting.get("attachment"), owner=user)
            setting["attachment"] = str(attachment.id)
        update_settings.append(setting)

    # make dict for easy updating
    dict_settings = {}
    for setting in widget.settings:
        dict_settings[setting.get("key")] = setting

    # update dict with new settings
    for update in update_settings:
        dict_settings[update.get("key")] = update

    # make new settings array
    new_settings = []
    for key in dict_settings:
        new_settings.append(dict_settings[key])

    # update widget
    widget.settings = new_settings

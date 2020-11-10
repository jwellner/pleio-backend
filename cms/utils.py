from cms.models import Page, Row, Column
from graphql import GraphQLError
from core.constances import COULD_NOT_FIND
from core.models import Widget
from wiki.models import Wiki


def order_positions(parent):
    """
    Order Rows, Columns or Widgets with same parent_id so that the positions are following numbers
    """

    if parent.type_to_string == 'page':
        children = Row.objects.filter(page=parent)

    if parent.type_to_string == 'row':
        children = Column.objects.filter(row=parent)

    if parent.type_to_string == 'column':
        children = Widget.objects.filter(column=parent)

    if parent.type_to_string == 'group':
        children = Widget.objects.filter(group=parent)

    if parent.type_to_string == 'wiki':
        children = Wiki.objects.filter(parent=parent)

    if not children:
        return

    sorted_children = sorted(children, key=lambda k: k.position)

    position = 0
    for child in sorted_children:
        child.position = position
        child.save()
        position = position + 1


def reorder_positions(obj, old_position, new_position):
    """
    Reorder Rows, Columns or Widgets with same parent
    """
    # pylint: disable=too-many-branches
    children = []

    if new_position is None:
        return

    if old_position == new_position:
        return

    if obj.type_to_string == 'page':
        children = Page.objects.filter(parent=obj.parent)

    if obj.type_to_string == 'wiki':
        children = Wiki.objects.filter(parent=obj.parent)

    if obj.type_to_string == 'row':
        children = Row.objects.filter(page=obj.page)

    if obj.type_to_string == 'column':
        children = Column.objects.filter(row=obj.row)

    if obj.type_to_string == 'widget' and obj.group:
        children = Widget.objects.filter(group=obj.group)

    if obj.type_to_string == 'widget' and not obj.group:
        children = Widget.objects.filter(column=obj.column)

    if not children:
        raise GraphQLError(COULD_NOT_FIND)

    # If no old_position provided, raise_one all children with same position or higher. Skip altered object.
    if old_position is None:
        for child in children:

            if child.position >= obj.position and child.id != obj.id:
                child.position = child.position + 1
                child.save()

    # If new_position is higher than old_position, lower the child with same or lower position as new position.
    # Skip altered object and children with position lower than old position..
    if old_position is not None and new_position > old_position:
        for child in children:
            if child.position <= new_position and child.position > old_position and child.id != obj.id:
                child.position = child.position - 1
                child.save()

    # If new_position is lower than old_position, raise the child with same or higer position as new position.
    # Skip altered object and children with position higher than old position.
    if old_position is not None and new_position < old_position:
        for child in children:
            if child.position >= new_position and child.position < old_position and child.id != obj.id:
                child.position = child.position + 1
                child.save()

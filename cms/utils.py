from cms.models import Row, Column
from graphql import GraphQLError
from core.constances import COULD_NOT_FIND


def order_positions(parent_id):
    """
    Order Rows, Columns or Widgets with same parent_id so that the positions are following numbers
    """

    children = Row.objects.filter(parent_id=parent_id)
    if not children:
        children = Column.objects.filter(parent_id=parent_id)

    if not children:
        raise GraphQLError(COULD_NOT_FIND)

    sorted_children = sorted(children, key=lambda k: k.position)

    position = 0
    for child in sorted_children:
        child.position = position
        child.save()
        position = position + 1


def reorder_positions(obj, old_position, new_position):
    """
    Reorder Rows, Columns or Widgets with same parent_id
    """

    if not new_position:
        return

    if old_position == new_position:
        return

    children = Row.objects.filter(parent_id=obj.parent_id)
    if not children:
        children = Column.objects.filter(parent_id=obj.parent_id)

    if not children:
        raise GraphQLError(COULD_NOT_FIND)

    # If no old_position provided, raise_one all children with same position or higher. Skip altered object.
    if not old_position:
        for child in children:

            if child.position >= obj.position and child.id != obj.id:
                child.position = child.position + 1
                child.save()

    # If new_position is higher than old_position, lower the child with same or lower position as new position.
    # Skip altered object and children with position lower than old position..
    if old_position and new_position > old_position:
        for child in children:
            if child.position <= new_position and not child.position < old_position and child.id != obj.id:
                child.position = child.position - 1
                child.save()

    # If new_position is lower than old_position, raise the child with same or higer position as new position.
    # Skip altered object and children with position higher than old position.
    if old_position and new_position < old_position:
        for child in children:
            if child.position >= new_position and not child.position > old_position and child.id != obj.id:
                child.position = child.position + 1
                child.save()

    order_positions(obj.parent_id)

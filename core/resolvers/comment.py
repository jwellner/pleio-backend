from ariadne import ObjectType
from core.resolvers import shared

comment = ObjectType("Comment")

@comment.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.can_write(info.context.user)

@comment.field("isBestAnswer")
def resolve_is_best_answer(obj, info):
    # pylint: disable=unused-argument
    if obj.container.best_answer and obj.container.best_answer == obj:
        return True
    return False


comment.set_field("description", shared.resolve_entity_description)
comment.set_field("richDescription", shared.resolve_entity_rich_description)
comment.set_field("timeCreated", shared.resolve_entity_time_created)
comment.set_field("timeUpdated", shared.resolve_entity_time_updated)
comment.set_field("canEdit", shared.resolve_entity_can_edit)
comment.set_field("votes", shared.resolve_entity_votes)
comment.set_field("hasVoted", shared.resolve_entity_has_voted)

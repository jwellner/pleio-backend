from ariadne import ObjectType
from core.resolvers import shared

comment = ObjectType("Comment")

@comment.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.can_write(info.context["request"].user)

@comment.field("isBestAnswer")
def resolve_is_best_answer(obj, info):
    # pylint: disable=unused-argument
    if hasattr(obj.container, 'best_answer') and obj.container.best_answer == obj:
        return True
    return False

@comment.field("ownerName")
def resolve_owner_name(obj, info):
    # pylint: disable=unused-argument
    if obj.owner:
        return obj.owner.name
    
    return obj.name


comment.set_field("description", shared.resolve_entity_description)
comment.set_field("richDescription", shared.resolve_entity_rich_description)
comment.set_field("timeCreated", shared.resolve_entity_time_created)
comment.set_field("timeUpdated", shared.resolve_entity_time_updated)
comment.set_field("canEdit", shared.resolve_entity_can_edit)
comment.set_field("votes", shared.resolve_entity_votes)
comment.set_field("hasVoted", shared.resolve_entity_has_voted)
comment.set_field("canComment", shared.resolve_entity_can_comment)
comment.set_field("comments", shared.resolve_entity_comments)
comment.set_field("commentCount", shared.resolve_entity_comment_count)

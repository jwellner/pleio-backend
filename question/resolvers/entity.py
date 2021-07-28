from ariadne import ObjectType
from core import config
from core.resolvers import shared

question = ObjectType("Question")

@question.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string

@question.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None

@question.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group

@question.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured

@question.field("isHighlighted")
def resolve_is_highlighted(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@question.field("isRecommended")
def resolve_is_recommended(obj, info):
    # pylint: disable=unused-argument
    return obj.is_recommended

@question.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@question.field("isClosed")
def resolve_is_closed(obj, info):
    # pylint: disable=unused-argument
    return obj.is_closed

@question.field("canClose")
def resolve_can_close(obj, info):
    # pylint: disable=unused-argument
    return obj.can_close(info.context["request"].user)

@question.field("canChooseBestAnswer")
def resolve_can_choose_best_answer(obj, info):
    # pylint: disable=unused-argument
    return obj.can_choose_best_answer(info.context["request"].user)

@question.field("comments")
def resolve_comments(obj, info):
    # pylint: disable=unused-argument
    comments = list(obj.comments.all())
    if obj.best_answer and config.QUESTIONER_CAN_CHOOSE_BEST_ANSWER:
        try:
            comments.remove(obj.best_answer)
            comments.insert(0, obj.best_answer)
        except Exception:
            pass
    return comments


question.set_field("guid", shared.resolve_entity_guid)
question.set_field("status", shared.resolve_entity_status)
question.set_field("title", shared.resolve_entity_title)
question.set_field("description", shared.resolve_entity_description)
question.set_field("richDescription", shared.resolve_entity_rich_description)
question.set_field("excerpt", shared.resolve_entity_excerpt)
question.set_field("tags", shared.resolve_entity_tags)
question.set_field("timeCreated", shared.resolve_entity_time_created)
question.set_field("timeUpdated", shared.resolve_entity_time_updated)
question.set_field("timePublished", shared.resolve_entity_time_published)
question.set_field("statusPublished", shared.resolve_entity_status_published)
question.set_field("canEdit", shared.resolve_entity_can_edit)
question.set_field("canComment", shared.resolve_entity_can_comment)
question.set_field("canVote", shared.resolve_entity_can_vote)
question.set_field("canBookmark", shared.resolve_entity_can_bookmark)
question.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
question.set_field("accessId", shared.resolve_entity_access_id)
question.set_field("writeAccessId", shared.resolve_entity_write_access_id)
question.set_field("featured", shared.resolve_entity_featured)
question.set_field("votes", shared.resolve_entity_votes)
question.set_field("hasVoted", shared.resolve_entity_has_voted)
question.set_field("canComment", shared.resolve_entity_can_comment)
question.set_field("commentCount", shared.resolve_entity_comment_count)
question.set_field("isFollowing", shared.resolve_entity_is_following)
question.set_field("views", shared.resolve_entity_views)
question.set_field("owner", shared.resolve_entity_owner)
question.set_field("isPinned", shared.resolve_entity_is_pinned)

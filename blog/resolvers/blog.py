from ariadne import ObjectType
from core.resolvers import shared

blog = ObjectType("Blog")

@blog.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return "blog"

@blog.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None

@blog.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group

@blog.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured

@blog.field("isHighlighted")
def resolve_is_highlighted(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@blog.field("isRecommended")
def resolve_is_recommended(obj, info):
    # pylint: disable=unused-argument
    return obj.is_recommended

@blog.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


blog.set_field("guid", shared.resolve_entity_guid)
blog.set_field("status", shared.resolve_entity_status)
blog.set_field("title", shared.resolve_entity_title)
blog.set_field("abstract", shared.resolve_entity_abstract)
blog.set_field("description", shared.resolve_entity_description)
blog.set_field("richDescription", shared.resolve_entity_rich_description)
blog.set_field("excerpt", shared.resolve_entity_excerpt)
blog.set_field("tags", shared.resolve_entity_tags)
blog.set_field("timeCreated", shared.resolve_entity_time_created)
blog.set_field("timeUpdated", shared.resolve_entity_time_updated)
blog.set_field("timePublished", shared.resolve_entity_time_published)
blog.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
blog.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
blog.set_field("statusPublished", shared.resolve_entity_status_published)
blog.set_field("canEdit", shared.resolve_entity_can_edit)
blog.set_field("canComment", shared.resolve_entity_can_comment)
blog.set_field("canVote", shared.resolve_entity_can_vote)
blog.set_field("canBookmark", shared.resolve_entity_can_bookmark)
blog.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
blog.set_field("accessId", shared.resolve_entity_access_id)
blog.set_field("writeAccessId", shared.resolve_entity_write_access_id)
blog.set_field("featured", shared.resolve_entity_featured)
blog.set_field("votes", shared.resolve_entity_votes)
blog.set_field("hasVoted", shared.resolve_entity_has_voted)
blog.set_field("canComment", shared.resolve_entity_can_comment)
blog.set_field("comments", shared.resolve_entity_comments)
blog.set_field("commentCount", shared.resolve_entity_comment_count)
blog.set_field("isFollowing", shared.resolve_entity_is_following)
blog.set_field("views", shared.resolve_entity_views)
blog.set_field("owner", shared.resolve_entity_owner)
blog.set_field("isPinned", shared.resolve_entity_is_pinned)

from ariadne import ObjectType
from core.resolvers import shared

discussion = ObjectType("Discussion")

@discussion.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return "discussion"

@discussion.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None

@discussion.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group

@discussion.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@discussion.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured


discussion.set_field("guid", shared.resolve_entity_guid)
discussion.set_field("status", shared.resolve_entity_status)
discussion.set_field("title", shared.resolve_entity_title)
discussion.set_field("description", shared.resolve_entity_description)
discussion.set_field("richDescription", shared.resolve_entity_rich_description)
discussion.set_field("excerpt", shared.resolve_entity_excerpt)
discussion.set_field("tags", shared.resolve_entity_tags)
discussion.set_field("timeCreated", shared.resolve_entity_time_created)
discussion.set_field("timeUpdated", shared.resolve_entity_time_updated)
discussion.set_field("timePublished", shared.resolve_entity_time_published)
discussion.set_field("statusPublished", shared.resolve_entity_status_published)
discussion.set_field("status", shared.resolve_entity_status)
discussion.set_field("canEdit", shared.resolve_entity_can_edit)
discussion.set_field("canComment", shared.resolve_entity_can_comment)
discussion.set_field("canVote", shared.resolve_entity_can_vote)
discussion.set_field("canBookmark", shared.resolve_entity_can_bookmark)
discussion.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
discussion.set_field("accessId", shared.resolve_entity_access_id)
discussion.set_field("writeAccessId", shared.resolve_entity_write_access_id)
discussion.set_field("featured", shared.resolve_entity_featured)
discussion.set_field("votes", shared.resolve_entity_votes)
discussion.set_field("hasVoted", shared.resolve_entity_has_voted)
discussion.set_field("canComment", shared.resolve_entity_can_comment)
discussion.set_field("comments", shared.resolve_entity_comments)
discussion.set_field("commentCount", shared.resolve_entity_comment_count)
discussion.set_field("isFollowing", shared.resolve_entity_is_following)
discussion.set_field("views", shared.resolve_entity_views)
discussion.set_field("owner", shared.resolve_entity_owner)
discussion.set_field("isPinned", shared.resolve_entity_is_pinned)

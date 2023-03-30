from ariadne import ObjectType
from core.resolvers import shared

status_update = ObjectType("StatusUpdate")


@status_update.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string


@status_update.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None


@status_update.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group


@status_update.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


status_update.set_field("guid", shared.resolve_entity_guid)
status_update.set_field("status", shared.resolve_entity_status)
status_update.set_field("title", shared.resolve_entity_title)
status_update.set_field("description", shared.resolve_entity_description)
status_update.set_field("richDescription", shared.resolve_entity_rich_description)
status_update.set_field("excerpt", shared.resolve_entity_excerpt)
status_update.set_field("tags", shared.resolve_entity_tags)
status_update.set_field("tagCategories", shared.resolve_entity_categories)
status_update.set_field("timeCreated", shared.resolve_entity_time_created)
status_update.set_field("timeUpdated", shared.resolve_entity_time_updated)
status_update.set_field("timePublished", shared.resolve_entity_time_published)
status_update.set_field("statusPublished", shared.resolve_entity_status_published)
status_update.set_field("canEdit", shared.resolve_entity_can_edit)
status_update.set_field("canComment", shared.resolve_entity_can_comment)
status_update.set_field("canVote", shared.resolve_entity_can_vote)
status_update.set_field("canBookmark", shared.resolve_entity_can_bookmark)
status_update.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
status_update.set_field("accessId", shared.resolve_entity_access_id)
status_update.set_field("writeAccessId", shared.resolve_entity_write_access_id)
status_update.set_field("votes", shared.resolve_entity_votes)
status_update.set_field("hasVoted", shared.resolve_entity_has_voted)
status_update.set_field("canComment", shared.resolve_entity_can_comment)
status_update.set_field("comments", shared.resolve_entity_comments)
status_update.set_field("commentCount", shared.resolve_entity_comment_count)
status_update.set_field("isFollowing", shared.resolve_entity_is_following)
status_update.set_field("views", shared.resolve_entity_views)
status_update.set_field("owner", shared.resolve_entity_owner)
status_update.set_field("isPinned", shared.resolve_entity_is_pinned)
status_update.set_field("lastSeen", shared.resolve_entity_last_seen)

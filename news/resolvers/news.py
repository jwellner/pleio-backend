from ariadne import ObjectType
from core.resolvers import shared

news = ObjectType("News")

@news.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string

@news.field("startDate")
def resolve_start_date(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in news"""
    return None

@news.field("endDate")
def resolve_end_date(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in news"""
    return None

@news.field("source")
def resolve_source(obj, info):
    # pylint: disable=unused-argument
    return obj.source

@news.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured

@news.field("isHighlighted")
def resolve_is_highlighted(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@news.field("isRecommended")
def resolve_is_recommended(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by news"""
    return False

@news.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


news.set_field("guid", shared.resolve_entity_guid)
news.set_field("status", shared.resolve_entity_status)
news.set_field("title", shared.resolve_entity_title)
news.set_field("description", shared.resolve_entity_description)
news.set_field("richDescription", shared.resolve_entity_rich_description)
news.set_field("excerpt", shared.resolve_entity_excerpt)
news.set_field("tags", shared.resolve_entity_tags)
news.set_field("timeCreated", shared.resolve_entity_time_created)
news.set_field("timeUpdated", shared.resolve_entity_time_updated)
news.set_field("timePublished", shared.resolve_entity_time_published)
news.set_field("statusPublished", shared.resolve_entity_status_published)
news.set_field("canEdit", shared.resolve_entity_can_edit)
news.set_field("canComment", shared.resolve_entity_can_comment)
news.set_field("canVote", shared.resolve_entity_can_vote)
news.set_field("canBookmark", shared.resolve_entity_can_bookmark)
news.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
news.set_field("accessId", shared.resolve_entity_access_id)
news.set_field("writeAccessId", shared.resolve_entity_write_access_id)
news.set_field("featured", shared.resolve_entity_featured)
news.set_field("votes", shared.resolve_entity_votes)
news.set_field("hasVoted", shared.resolve_entity_has_voted)
news.set_field("canComment", shared.resolve_entity_can_comment)
news.set_field("comments", shared.resolve_entity_comments)
news.set_field("commentCount", shared.resolve_entity_comment_count)
news.set_field("isFollowing", shared.resolve_entity_is_following)
news.set_field("views", shared.resolve_entity_views)
news.set_field("owner", shared.resolve_entity_owner)
news.set_field("isPinned", shared.resolve_entity_is_pinned)

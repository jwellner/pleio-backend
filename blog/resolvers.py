from ariadne import ObjectType
from django.utils.text import slugify
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
    """Deprecated: only used by news"""
    return False

@blog.field("isHighlighted")
def resolve_is_highlighted(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not used in frontend"""
    return False

@blog.field("isRecommended")
def resolve_is_recommended(obj, info):
    # pylint: disable=unused-argument
    return obj.is_recommended

@blog.field("isBookmarked")
def resolve_is_bookmarked(obj, info):
    # pylint: disable=unused-argument
    return False

@blog.field("isFollowing")
def resolve_is_following(obj, info):
    # pylint: disable=unused-argument
    return False

@blog.field("hasVoted")
def resolve_has_voted(obj, info):
    # pylint: disable=unused-argument
    return False

@blog.field("votes")
def resolve_votes(obj, info):
    # pylint: disable=unused-argument
    return 0

@blog.field("views")
def resolve_views(obj, info):
    # pylint: disable=unused-argument
    return 0

@blog.field("owner")
def resolve_owner(obj, info):
    # pylint: disable=unused-argument
    return obj.owner

@blog.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument

    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return '{}/blog/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()

@blog.field("comments")
def resolve_comments(obj, info):
    # pylint: disable=unused-argument
    return obj.comments.all()

@blog.field("commentCount")
def resolve_comment_count(obj, info):
    # pylint: disable=unused-argument
    return obj.comments.all().count()


blog.set_field("guid", shared.resolve_entity_guid)
blog.set_field("status", shared.resolve_entity_status)
blog.set_field("description", shared.resolve_entity_description)
blog.set_field("richDescription", shared.resolve_entity_rich_description)
blog.set_field("excerpt", shared.resolve_entity_excerpt)
blog.set_field("tags", shared.resolve_entity_tags)
blog.set_field("timeCreated", shared.resolve_entity_time_created)
blog.set_field("timeUpdated", shared.resolve_entity_time_updated)
blog.set_field("canEdit", shared.resolve_entity_can_edit)
blog.set_field("canComment", shared.resolve_entity_can_comment)
blog.set_field("canVote", shared.resolve_entity_can_vote)
blog.set_field("canBookmark", shared.resolve_entity_can_bookmark)
blog.set_field("accessId", shared.resolve_entity_access_id)
blog.set_field("writeAccessId", shared.resolve_entity_write_access_id)
blog.set_field("featured", shared.resolve_entity_featured)

resolvers = [blog]

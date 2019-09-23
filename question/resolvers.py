from ariadne import ObjectType
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from core.resolvers import shared
from core.lib import remove_none_from_dict
from core.models import Comment
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from question.models import Question

question = ObjectType("Question")
mutation = ObjectType("Mutation")

@question.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return "blog"

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
    """Deprecated: only used by news"""
    return False

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

    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return '{}/questions/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()

@question.field("isClosed")
def resolve_is_closed(obj, info):
    # pylint: disable=unused-argument
    return obj.is_closed

@question.field("canClose")
def resolve_can_close(obj, info):
    # pylint: disable=unused-argument
    return obj.can_close(info.context.user)

@question.field("canChooseBestAnswer")
def resolve_can_choose_best_answer(obj, info):
    # pylint: disable=unused-argument
    return obj.can_choose_best_answer(info.context.user)


question.set_field("guid", shared.resolve_entity_guid)
question.set_field("status", shared.resolve_entity_status)
question.set_field("title", shared.resolve_entity_title)
question.set_field("description", shared.resolve_entity_description)
question.set_field("richDescription", shared.resolve_entity_rich_description)
question.set_field("excerpt", shared.resolve_entity_excerpt)
question.set_field("tags", shared.resolve_entity_tags)
question.set_field("timeCreated", shared.resolve_entity_time_created)
question.set_field("timeUpdated", shared.resolve_entity_time_updated)
question.set_field("canEdit", shared.resolve_entity_can_edit)
question.set_field("canComment", shared.resolve_entity_can_comment)
question.set_field("canVote", shared.resolve_entity_can_vote)
question.set_field("canBookmark", shared.resolve_entity_can_bookmark)
question.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
question.set_field("accessId", shared.resolve_entity_access_id)
question.set_field("writeAccessId", shared.resolve_entity_write_access_id)
question.set_field("votes", shared.resolve_entity_votes)
question.set_field("hasVoted", shared.resolve_entity_has_voted)
question.set_field("canComment", shared.resolve_entity_can_comment)
question.set_field("comments", shared.resolve_entity_comments)
question.set_field("commentCount", shared.resolve_entity_comment_count)
question.set_field("isFollowing", shared.resolve_entity_is_following)
question.set_field("views", shared.resolve_entity_views)
question.set_field("owner", shared.resolve_entity_owner)

@mutation.field("toggleBestAnswer")
def resolve_toggle_best_answer(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        comment = Comment.objects.get(id=clean_input.get("guid"))
        question = Question.objects.visible(user).get(id=comment.object_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not question.can_choose_best_answer(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if question.best_answer == comment:
        question.best_answer = None
    else:
        question.best_answer = comment
    question.save()

    return {
        "entity": question
    }

@mutation.field("toggleIsClosed")
def resolve_toggle_item_closed(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        question = Question.objects.visible(user).get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not question.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    question.is_closed = not question.is_closed
    question.save()

    return {
        "entity": question
    }


resolvers = [question, mutation]

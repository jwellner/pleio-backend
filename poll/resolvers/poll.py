from ariadne import ObjectType
from core.resolvers import shared


poll = ObjectType("Poll")


@poll.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@poll.field("hasVoted")
def resolve_has_votes(obj, info):
    # pylint: disable=unused-argument
    for choice in obj.choices.all():
        if choice.has_voted(info.context["request"].user):
            return True
    return False

@poll.field("choices")
def resolve_choices(obj, info):
    # pylint: disable=unused-argument
    return obj.choices.all()


poll.set_field("guid", shared.resolve_entity_guid)
poll.set_field("status", shared.resolve_entity_status)
poll.set_field("title", shared.resolve_entity_title)
poll.set_field("timeCreated", shared.resolve_entity_time_created)
poll.set_field("timeUpdated", shared.resolve_entity_time_updated)
poll.set_field("canEdit", shared.resolve_entity_can_edit)
poll.set_field("accessId", shared.resolve_entity_access_id)
poll.set_field("isPinned", shared.resolve_entity_is_pinned)


poll_choice = ObjectType("PollChoice")

@poll_choice.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@poll_choice.field("text")
def resolve_text(obj, info):
    # pylint: disable=unused-argument
    return obj.text

@poll_choice.field("votes")
def resolve_votes(obj, info):
    # pylint: disable=unused-argument
    return obj.vote_count()

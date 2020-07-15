from ariadne import ObjectType
from .poll import poll, poll_choice
from .mutation import resolve_add_poll, resolve_edit_poll, resolve_vote_on_poll

mutation = ObjectType("Mutation")

mutation.set_field("addPoll", resolve_add_poll)
mutation.set_field("editPoll", resolve_edit_poll)
mutation.set_field("voteOnPoll", resolve_vote_on_poll)

resolvers = [poll, poll_choice, mutation]

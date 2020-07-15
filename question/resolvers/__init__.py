from ariadne import ObjectType, InterfaceType
from .entity import question
from .mutation import resolve_toggle_best_answer, resolve_toggle_item_closed

mutation = ObjectType("Mutation")
mutation.set_field("toggleBestAnswer", resolve_toggle_best_answer)
mutation.set_field("toggleIsClosed", resolve_toggle_item_closed)

resolvers = [question, mutation]

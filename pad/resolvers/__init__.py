from ariadne import ObjectType
from .pad import pad
from .mutation import resolve_add_pad, resolve_edit_pad

mutation = ObjectType("Mutation")

mutation.set_field("addPad", resolve_add_pad)
mutation.set_field("editPad", resolve_edit_pad)

resolvers = [pad, mutation]

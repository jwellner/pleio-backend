from ariadne import ObjectType
from .task import task
from .mutation import resolve_edit_task_state

mutation = ObjectType("Mutation")
mutation.set_field("editTask", resolve_edit_task_state)

resolvers = [mutation, task]

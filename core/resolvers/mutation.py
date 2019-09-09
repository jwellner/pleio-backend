from ariadne import ObjectType
from .mutation_add_group import resolve_add_group
from .mutation_edit_group import resolve_edit_group
from .mutation_join_group import resolve_join_group
from .mutation_leave_group import resolve_leave_group
from .mutation_add_entity import resolve_add_entity
from .mutation_edit_entity import resolve_edit_entity
from .mutation_delete_entity import resolve_delete_entity


mutation = ObjectType("Mutation")
mutation.set_field("addGroup", resolve_add_group)
mutation.set_field("editGroup", resolve_edit_group)
mutation.set_field("joinGroup", resolve_join_group)
mutation.set_field("leaveGroup", resolve_leave_group)

mutation.set_field("addEntity", resolve_add_entity)
mutation.set_field("editEntity", resolve_edit_entity)
mutation.set_field("deleteEntity", resolve_delete_entity)

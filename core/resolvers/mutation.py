from ariadne import ObjectType
from .mutation_add_group import resolve_add_group
from .mutation_edit_group import resolve_edit_group
from .mutation_join_group import resolve_join_group
from .mutation_leave_group import resolve_leave_group
from .mutation_add_entity import resolve_add_entity
from .mutation_edit_entity import resolve_edit_entity
from .mutation_delete_entity import resolve_delete_entity
from .mutation_vote import resolve_vote
from .mutation_bookmark import resolve_bookmark
from .mutation_follow import resolve_follow
from .mutation_send_message_to_user import resolve_send_message_to_user
from .mutation_toggle_request_delete_user import resolve_toggle_request_delete_user
from .mutation_mark_as_read import resolve_mark_as_read, resolve_mark_all_as_read


mutation = ObjectType("Mutation")
mutation.set_field("addGroup", resolve_add_group)
mutation.set_field("editGroup", resolve_edit_group)
mutation.set_field("joinGroup", resolve_join_group)
mutation.set_field("leaveGroup", resolve_leave_group)

mutation.set_field("addEntity", resolve_add_entity)
mutation.set_field("editEntity", resolve_edit_entity)
mutation.set_field("deleteEntity", resolve_delete_entity)

mutation.set_field("vote", resolve_vote)

mutation.set_field("bookmark", resolve_bookmark)
mutation.set_field("follow", resolve_follow)

mutation.set_field("sendMessageToUser", resolve_send_message_to_user)
mutation.set_field("toggleRequestDeleteUser", resolve_toggle_request_delete_user)

mutation.set_field("markAsRead", resolve_mark_as_read)
mutation.set_field("markAllAsRead", resolve_mark_all_as_read)

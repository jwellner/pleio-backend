from ariadne import ObjectType
from cms.resolvers.mutation_add_page import resolve_add_page
from cms.resolvers.mutation_edit_page import resolve_edit_page
from cms.resolvers.mutation_add_row import resolve_add_row
from cms.resolvers.mutation_edit_row import resolve_edit_row
from cms.resolvers.mutation_delete_row import resolve_delete_row


mutation = ObjectType("Mutation")

mutation.set_field("addPage", resolve_add_page)
mutation.set_field("editPage", resolve_edit_page)
mutation.set_field("addRow", resolve_add_row)
mutation.set_field("editRow", resolve_edit_row)
mutation.set_field("deleteRow", resolve_delete_row)

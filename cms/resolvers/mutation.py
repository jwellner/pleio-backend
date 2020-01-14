from ariadne import ObjectType
from cms.resolvers.mutation_add_page import resolve_add_page
from cms.resolvers.mutation_edit_page import resolve_edit_page
from cms.resolvers.mutation_add_row import resolve_add_row
from cms.resolvers.mutation_edit_row import resolve_edit_row
from cms.resolvers.mutation_delete_row import resolve_delete_row
from cms.resolvers.mutation_add_column import resolve_add_column
from cms.resolvers.mutation_edit_column import resolve_edit_column
from cms.resolvers.mutation_delete_column import resolve_delete_column
from cms.resolvers.mutation_add_widget import resolve_add_widget
from cms.resolvers.mutation_edit_widget import resolve_edit_widget
from cms.resolvers.mutation_delete_widget import resolve_delete_widget


mutation = ObjectType("Mutation")

mutation.set_field("addPage", resolve_add_page)
mutation.set_field("editPage", resolve_edit_page)
mutation.set_field("addRow", resolve_add_row)
mutation.set_field("editRow", resolve_edit_row)
mutation.set_field("deleteRow", resolve_delete_row)
mutation.set_field("addColumn", resolve_add_column)
mutation.set_field("editColumn", resolve_edit_column)
mutation.set_field("deleteColumn", resolve_delete_column)
mutation.set_field("addWidget", resolve_add_widget)
mutation.set_field("editWidget", resolve_edit_widget)
mutation.set_field("deleteWidget", resolve_delete_widget)

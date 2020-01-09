from ariadne import ObjectType
from cms.resolvers.mutation_add_page import resolve_add_page
from cms.resolvers.mutation_edit_page import resolve_edit_page

mutation = ObjectType("Mutation")

mutation.set_field("addPage", resolve_add_page)
mutation.set_field("editPage", resolve_edit_page)

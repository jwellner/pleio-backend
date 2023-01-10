from ariadne import ObjectType

from .mutation_add import add_datahub_external_content_source
from .mutation_edit import edit_datahub_external_content_source
from .mutation_delete import resolve_delete_external_content_source

mutation = ObjectType("Mutation")

mutation.set_field('deleteExternalContentSource', resolve_delete_external_content_source)
mutation.set_field('addDatahubExternalContentSource', add_datahub_external_content_source)
mutation.set_field('editDatahubExternalContentSource', edit_datahub_external_content_source)

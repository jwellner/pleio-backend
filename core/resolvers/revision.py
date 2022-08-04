from ariadne import ObjectType
from core.resolvers import shared

revision = ObjectType("Revision")

revision.set_field("timeCreated", shared.resolve_entity_time_created)
revision.set_field("timeUpdated", shared.resolve_entity_time_updated)
from ariadne import InterfaceType

entity = InterfaceType("Entity")

@entity.type_resolver
def resolve_entity_type(obj, *_):
    if obj._meta.object_name == "FileFolder":
        return obj.type

    return obj._meta.object_name

@entity.field("status")
def resolve_entity_status(obj, info):
    # pylint: disable=unused-argument
    if not obj:
        return 404
    return 200

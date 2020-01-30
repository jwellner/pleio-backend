from ariadne import ObjectType

subgroup = ObjectType("Subgroup")

@subgroup.field("id")
def resolve_id(obj, info):
    # pylint: disable=unused-argument
    return obj.id

@subgroup.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name

@subgroup.field("members")
def resolve_members(obj, info):
    # pylint: disable=unused-argument
    return obj.members.all()

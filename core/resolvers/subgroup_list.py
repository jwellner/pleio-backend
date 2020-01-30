from ariadne import ObjectType


subgroup_list = ObjectType("SubgroupList")

@subgroup_list.field("total")
def resolve_total(obj, info):
    # pylint: disable=unused-argument
    return len(obj)

@subgroup_list.field("edges")
def resolve_edges(obj, info):
    # pylint: disable=unused-argument
    return obj

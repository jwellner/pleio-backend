from ariadne import ObjectType

tag_category = ObjectType("TagCategory")


@tag_category.field("restrictContentTypes")
def resolve_restrict_content_types(obj, _):
    return obj.get('restrictContentTypes', False)

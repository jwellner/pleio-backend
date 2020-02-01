from ariadne import ObjectType

email_overview = ObjectType("EmailOverview")

@email_overview.field("frequency")
def resolve_frequency(obj, info):
    # pylint: disable=unused-argument
    return obj.overview_email_interval

@email_overview.field("tags")
def resolve_tags(obj, info):
    # pylint: disable=unused-argument
    return obj.overview_email_tags

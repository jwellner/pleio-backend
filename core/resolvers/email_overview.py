from ariadne import ObjectType
from core import config

email_overview = ObjectType("EmailOverview")

@email_overview.field("frequency")
def resolve_frequency(obj, info):
    # pylint: disable=unused-argument
    if obj.overview_email_interval:
        return obj.overview_email_interval
    return config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY

@email_overview.field("tags")
def resolve_tags(obj, info):
    # pylint: disable=unused-argument
    return obj.overview_email_tags

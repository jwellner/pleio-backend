from ariadne import InterfaceType, ObjectType

from external_content.api_handlers.datahub import ApiHandler as DatahubApiHandler
from external_content.models import ExternalContentSource

external_content_source = InterfaceType("ExternalContentSource")
datahub_source = ObjectType("DatahubContentSource")


@external_content_source.type_resolver
def type_resolver(obj, *_):
    assert isinstance(obj, ExternalContentSource)
    if obj.handler_id == DatahubApiHandler.ID:
        return "DatahubContentSource"
    return "DefaultExternalContentSource"


@external_content_source.field("key")
def resolve_key(obj, info):
    # pylint: disable=unused-argument
    return obj.id


@external_content_source.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name


@external_content_source.field("pluralName")
def resolve_plural_name(obj, info):
    # pylint: disable=unused-argument
    return obj.plural_name


@external_content_source.field("handlerId")
def resolve_handler(obj, info):
    # pylint: disable=unused-argument
    return obj.handler_id


datahub_source.set_field("key", resolve_key)
datahub_source.set_field("name", resolve_name)
datahub_source.set_field("pluralName", resolve_plural_name)
datahub_source.set_field("handlerId", resolve_handler)


@datahub_source.field("apiUrl")
def resolve_api_url(obj, info):
    # pylint: disable=unused-argument
    return obj.settings['apiUrl']

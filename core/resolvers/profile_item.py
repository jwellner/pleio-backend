from ariadne import ObjectType
from core.lib import get_access_id, get_field_type

profile_item = ObjectType("ProfileItem")


@profile_item.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.id


@profile_item.field("key")
def resolve_key(obj, info):
    # pylint: disable=unused-argument
    return obj.key


@profile_item.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name


@profile_item.field("isFilter")
def resolve_is_filter(obj, info):
    # pylint: disable=unused-argument
    return obj.is_filter


@profile_item.field("isInOverview")
def resolve_is_in_overview(obj, info):
    # pylint: disable=unused-argument
    return obj.is_in_overview


@profile_item.field("isOnVcard")
def resolve_is_on_vcard(obj, info):
    # pylint: disable=unused-argument
    return obj.is_on_vcard


@profile_item.field("value")
def resolve_value(obj, info):
    # pylint: disable=unused-argument
    return obj.value


@profile_item.field("accessId")
def resolve_access_id(obj, info):
    # pylint: disable=unused-argument
    return get_access_id(obj.read_access)


@profile_item.field("category")
def resolve_category(obj, info):
    # pylint: disable=unused-argument
    return obj.category


@profile_item.field("fieldType")
def resolve_field_type(obj, info):
    # pylint: disable=unused-argument
    return get_field_type(obj.field_type)


@profile_item.field("fieldOptions")
def resolve_field_options(obj, info):
    # pylint: disable=unused-argument
    return obj.field_options


@profile_item.field("isEditable")
def resolve_is_editable(obj, info):
    # pylint: disable=unused-argument
    return obj.is_editable_by_user


@profile_item.field("isFilterable")
def resolve_is_filterable(obj, info):
    # pylint: disable=unused-argument
    return obj.is_filterable


@profile_item.field("isInOnboarding")
def resolve_is_in_onboarding(obj, info):
    # pylint: disable=unused-argument
    return obj.is_in_onboarding


@profile_item.field("isMandatory")
def resolve_is_mandatory(obj, info):
    # pylint: disable=unused-argument
    return obj.is_mandatory


@profile_item.field("profileFieldValidator")
def resolve_profile_field_validator(obj, info):
    # pylint: disable=unused-argument
    return obj.validators.first()

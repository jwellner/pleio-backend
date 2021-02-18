from ariadne import ObjectType

profile_field_validator = ObjectType("ProfileFieldValidator")

@profile_field_validator.field("id")
def resolve_id(obj, info):
    # pylint: disable=unused-argument
    return obj.id

@profile_field_validator.field("type")
def resolve_type(obj, info):
    # pylint: disable=unused-argument
    return obj.validator_type


@profile_field_validator.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name

@profile_field_validator.field("validationString")
def resolve_validation_string(obj, info):
    # pylint: disable=unused-argument
    if obj.validator_type not in ['inList']:
        return obj.validator_data

    return None

@profile_field_validator.field("validationList")
def resolve_validation_list(obj, info):
    # pylint: disable=unused-argument
    if obj.validator_type in ['inList']:
        return obj.validator_data
    return None

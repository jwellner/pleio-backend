import logging
import csv
import codecs
from graphql import GraphQLError
from core.models import ProfileFieldValidator
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_VALUE, COULD_NOT_FIND
from core.lib import remove_none_from_dict
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

def resolve_edit_site_setting_profile_field_validator(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    try:
        validator = ProfileFieldValidator.objects.get(id=clean_input.get('id'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    validator_data = [] if validator.validator_type == "inList" else clean_input.get("validationString", "")

    if validator.validator_type == "inList":

        if 'validationListFile' in clean_input:
            validator_data = []
            try:
                csv_file = clean_input.get("validationListFile")
                csv_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=';')

                for row in csv_reader:
                    if row[0]: # skip empy rows
                        validator_data.append(row[0])

            except Exception as e:
                logger.error(e)
                raise GraphQLError(INVALID_VALUE)

            validator.validator_data = validator_data
    else:
        if 'validationString' in clean_input:
            validator.validator_data = clean_input.get("validationString")

    if 'name' in clean_input:
        validator.name = clean_input.get("name")

    validator.save()

    return {
        "profileFieldValidator": validator
    }

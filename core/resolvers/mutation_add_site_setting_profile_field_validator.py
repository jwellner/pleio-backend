import logging
import csv
import codecs
from graphql import GraphQLError
from core.models import ProfileFieldValidator
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_TYPE, NO_FILE, INVALID_VALUE
from core.lib import clean_graphql_input

logger = logging.getLogger(__name__)

def resolve_add_site_setting_profile_field_validator(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    if clean_input.get("type") not in ["inList"]:
        raise GraphQLError(INVALID_TYPE)

    validator_data = [] if clean_input.get("type") == "inList" else clean_input.get("validationString", "")

    if clean_input.get("type") == "inList":
        if not clean_input.get("validationListFile"):
            raise GraphQLError(NO_FILE)
        
        try:
            csv_file = clean_input.get("validationListFile")
            csv_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=';')

            for row in csv_reader:
                if row[0]: # skip empty rows
                    validator_data.append(row[0])

        except Exception as e:
            logger.error(e)
            raise GraphQLError(INVALID_VALUE)

    validator = ProfileFieldValidator.objects.create(
        name=clean_input.get("name"),
        validator_type=clean_input.get("type"),
        validator_data=validator_data
    )

    return {
        "profileFieldValidator": validator
    }

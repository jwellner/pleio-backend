import csv
import codecs
import os
import tempfile
from graphql import GraphQLError
from django.utils.translation import ugettext_lazy
from core import config
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_KEY
from core.lib import remove_none_from_dict, get_tmp_file_path, tenant_schema
from core.models import ProfileField
from core.tasks import import_users

def get_user_fields():
    # user fields
    user_fields = [
        {"value": "id", "label": "guid"},
        {"value": "email", "label": ugettext_lazy("email")},
        {"value": "name", "label": ugettext_lazy("name")}
    ]

    for field in ProfileField.objects.all():
        user_fields.append({"value": str(field.id), "label": field.name})

    return user_fields


def get_access_ids():
    # get access ids
    accessIdOptions = [
            {"value": 0, "label": ugettext_lazy("Just me")},
            {"value": 1, "label": ugettext_lazy("Logged in users")}
        ]
    if not config.IS_CLOSED:
        accessIdOptions.append({"value": 2, "label": ugettext_lazy("Public")})

    return accessIdOptions


def resolve_import_users_step_1(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    csv_file = clean_input.get("usersCsv")
    csv_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=';')

    csv_header = []
    for row in csv_reader:
        csv_header = row
        break

    # Save file in temp user folder
    temp_file_path = get_tmp_file_path(user, ".csv")

    with open(temp_file_path, 'wb+') as destination:
        for chunk in csv_file.chunks():
            destination.write(chunk)

    # This can later be a database record?
    import_id = os.path.basename(temp_file_path)

    return {
        "importId": import_id,
        "csvColumns": csv_header,
        "userFields": get_user_fields(),
        "accessIdOptions": get_access_ids()
    }


def resolve_import_users_step_2(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    # Validate importId
    csv_location = os.path.join(tempfile.gettempdir(), tenant_schema(), user.guid, clean_input.get("importId"))

    if not os.path.isfile(csv_location):
        raise GraphQLError(INVALID_KEY)

    valid_column_values = []

    with open(csv_location, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            valid_column_values = row
            break
    
    valid_user_field_values = [d['value'] for d in get_user_fields() if 'value' in d]
    valid_access_id_values = [d['value'] for d in get_access_ids() if 'value' in d]

    fields = clean_input.get("fields")

    for field in fields:
        if field["userField"] not in valid_user_field_values:
            raise GraphQLError('invalid_user_field')
        if field['userField'] not in ['id', 'name', 'email'] and field["accessId"] not in valid_access_id_values:
            raise GraphQLError('invalid_access_id')
        if field["csvColumn"] not in valid_column_values:
            raise GraphQLError('invalid_csv_column')
        if 'forceAccess' not in field:
            field['forceAccess'] = False

    import_users.delay(tenant_schema(), fields, csv_location, user.guid)

    return {
        "success": True
    }

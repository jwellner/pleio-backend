from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from core.constances import COULD_NOT_FIND

from core.resolvers import shared
from core.lib import clean_graphql_input


from tenants.models import AgreementVersion, AgreementAccept, Client

def resolve_sign_site_agreement_version(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_administrator(user)

    try:
        agreement_version = AgreementVersion.objects.get(id=clean_input.get("id", None))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if agreement_version.accepted_for_tenant:
        raise GraphQLError("already_accepted")

    if not clean_input.get("accept"):
        raise GraphQLError("not_accepted")

    tenant = Client.objects.get(schema_name=connection.schema_name)

    AgreementAccept.objects.create(
        client=tenant,
        agreement_version=agreement_version,
        accept_name=user.name,
        accept_user_id=user.id
    )

    return {
        "siteAgreementVersion": agreement_version
    }

import os
from tenants.models import Agreement
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES
from core.models.agreement import CustomAgreement
from graphql import GraphQLError


def resolve_site_agreements(_, info):
    # pylint: disable=unused-argument

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    return Agreement.objects.all()

def resolve_site_custom_agreements(_, info):
    # pylint: disable=unused-argument

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    agreements = CustomAgreement.objects.all()
    custom_agreements = []
    for agreement in agreements:
        custom_agreements.append({
            'name': agreement.name,
            'fileName': os.path.basename(agreement.document.name),
            'url': agreement.url
        })
    return custom_agreements

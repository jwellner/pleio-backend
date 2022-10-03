from ariadne import ObjectType

site_agreement_version = ObjectType("SiteAgreementVersion")


@site_agreement_version.field("version")
def resolve_version(obj, info):
    # pylint: disable=unused-argument
    return obj.version


@site_agreement_version.field("document")
def resolve_document(obj, info):
    # pylint: disable=unused-argument
    return obj.get_absolute_url()


@site_agreement_version.field("accepted")
def resolve_accepted(obj, info):
    # pylint: disable=unused-argument
    return bool(obj.accepted_for_current_tenant)


@site_agreement_version.field("acceptedBy")
def resolve_accepted_by(obj, info):
    # pylint: disable=unused-argument
    if obj.accepted_for_current_tenant:
        return obj.accepted_for_current_tenant.accept_name

    return None


@site_agreement_version.field("acceptedDate")
def resolve_accepted_date(obj, info):
    # pylint: disable=unused-argument
    if obj.accepted_for_current_tenant:
        return obj.accepted_for_current_tenant.created_at

    return None

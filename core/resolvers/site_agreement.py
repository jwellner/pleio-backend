from ariadne import ObjectType

site_agreement = ObjectType("SiteAgreement")


@site_agreement.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name


@site_agreement.field("description")
def resolve_description(obj, info):
    # pylint: disable=unused-argument
    return obj.description


@site_agreement.field("accepted")
def resolve_accepted(obj, info):
    # pylint: disable=unused-argument
    return obj.latest_accepted_for_current_tenant


@site_agreement.field("versions")
def resolve_versions(obj, info):
    # pylint: disable=unused-argument
    return obj.versions.all()


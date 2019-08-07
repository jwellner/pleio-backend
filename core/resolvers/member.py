from ariadne import ObjectType

member = ObjectType("Member")

@member.field("role")
def resolve_role(obj, info):
    # pylint: disable=unused-argument
    return obj.type

@member.field("email")
def resolve_email(obj, info):
    # pylint: disable=unused-argument
    return obj.user.email

@member.field("user")
def resolve_user(obj, info):
    # pylint: disable=unused-argument
    return obj.user

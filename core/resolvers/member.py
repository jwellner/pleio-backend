from ariadne import ObjectType

member = ObjectType("Member")

@member.field("role")
def resolve_role(obj, info):
    # pylint: disable=unused-argument
    return obj.type

@member.field("email")
def resolve_email(obj, info):
    # pylint: disable=unused-argument

    request_user = info.context["request"].user

    if obj.user == request_user or obj.group.can_write(request_user):
        return obj.user.email
    return None

@member.field("user")
def resolve_user(obj, info):
    # pylint: disable=unused-argument
    return obj.user

@member.field("memberSince")
def resolve_member_since(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at

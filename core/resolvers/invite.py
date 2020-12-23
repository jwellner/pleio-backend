from ariadne import ObjectType


invite = ObjectType("Invite")

@invite.field("id")
def resolve_invite_id(obj, info):
    # pylint: disable=unused-argument
    return obj.id

@invite.field("timeCreated")
def resolve_invite_time_created(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at

@invite.field("invited")
def resolve_invite_invited(obj, info):
    # pylint: disable=unused-argument
    if hasattr(obj, 'invited'):
        return obj.invited
    return True

@invite.field("user")
def resolve_invite_user(obj, info):
    # pylint: disable=unused-argument
    return obj.invited_user

@invite.field("email")
def resolve_invite_email(obj, info):
    # pylint: disable=unused-argument

    if obj.invited_user:
        return obj.invited_user.email

    return obj.email

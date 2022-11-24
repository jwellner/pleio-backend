from core.models import ProfileSet
from core.resolvers import shared
from user.models import User


def resolve_mutation_add_profileset_manager(_, info, userGuid, profileSetGuid):
    acting_user = info.context["request"].user

    shared.assert_authenticated(acting_user)
    shared.assert_administrator(acting_user)

    user = User.objects.get(id=userGuid)
    profile_set = ProfileSet.objects.get(id=profileSetGuid)

    profile_set.users.add(user)

    return {
        'user': user,
        'profileSet': profile_set
    }


def resolve_mutation_remove_profileset_manager(_, info, userGuid, profileSetGuid):
    acting_user = info.context["request"].user

    shared.assert_authenticated(acting_user)
    shared.assert_administrator(acting_user)

    user = User.objects.get(id=userGuid)
    profile_set = ProfileSet.objects.get(id=profileSetGuid)

    profile_set.users.remove(user)

    return {
        'user': user,
        'profileSet': profile_set
    }

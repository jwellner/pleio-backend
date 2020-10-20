from core.constances import USER_ROLES

def resolve_viewer(_, info):
    user = info.context["request"].user
    banned = False
    try:
        if 'pleio_user_is_banned' in info.context["request"].session:
            banned = True
    except Exception:
        pass
    if not user.is_authenticated:
        return {
            'guid': 'viewer:0',
            'loggedIn': False,
            'isSubEditor': False,
            'isAdmin': False,
            'isBanned': banned,
            'tags': [],
            'user': {
                'guid': '0'
            }
        }

    return {
        'guid': 'viewer:{}'.format(user.id),
        'loggedIn': True,
        'isSubEditor': user.has_role(USER_ROLES.EDITOR),
        'isAdmin': user.has_role(USER_ROLES.ADMIN),
        'isBanned': banned,
        'tags': []
    }

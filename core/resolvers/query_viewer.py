def resolve_viewer(_, info):
    user = info.context.user

    if not user.is_authenticated:
        return {
            'guid': 'viewer:0',
            'loggedIn': False,
            'isSubEditor': False,
            'isAdmin': False,
            'tags': [],
            'canWriteToContainer': False,
            'user': {
                'guid': '0'
            }
        }

    return {
        'guid': 'viewer:{}'.format(user.id),
        'loggedIn': True,
        'isSubEditor': user.is_admin,
        'isAdmin': user.is_admin,
        'tags': [],
        'canWriteToContainer': True
    }

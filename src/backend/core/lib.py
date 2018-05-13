def get_acl(user):
    acl = ['public']

    if user.is_authenticated:
        acl.append('logged_in')
        acl.append('user:{}'.format(user.id))

    if user.groups:
        acl = acl + ['group:{}'.format(group.id) for group in user.groups.all()]

    return acl
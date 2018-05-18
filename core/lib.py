def get_acl(user):
    acl = set(['public'])

    if user.is_authenticated:
        acl.add('logged_in')
        acl.add('user:{}'.format(user.id))

    if user.groups:
        groups = set('group:{}'.format(group.id) for group in user.groups.all())
        acl = acl.union(groups)

    return acl

def get_id(input_id):
    splitted_id = input_id.split(':')
    return splitted_id[1]
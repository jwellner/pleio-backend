from .enums import ACCESS_TYPE

def get_acl(user):
    acl = set([ACCESS_TYPE.public])

    if user.is_authenticated:
        acl.add(ACCESS_TYPE.logged_in)
        acl.add(ACCESS_TYPE.user.format(user.id))

    if user.groups:
        groups = set(
            ACCESS_TYPE.group.format(group.id) for group in user.groups.all()
            )
        acl = acl.union(groups)

    return acl


def get_type(input_id):
    splitted_id = input_id.split(':')
    return splitted_id[0]


def get_id(input_id):
    splitted_id = input_id.split(':')
    return splitted_id[1]

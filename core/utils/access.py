def get_read_access_weight(instance):
    return get_access_weight(instance, 'read_access')


def get_write_access_weight(instance):
    return get_access_weight(instance, 'write_access')


def get_access_weight(instance, access_property):
    """ #1: Eigenaar
        #2: Subgroep
        #3: Groep
        #4: Ingelogd
        #5: Publiek
    """

    if test_read_access(instance, access_property, any_match=lambda access: access == 'public'):
        return 5
    if test_read_access(instance, access_property, any_match=lambda access: access == 'logged_in'):
        return 4
    if test_read_access(instance, access_property, any_match=lambda access: access[:6] == 'group:'):
        return 3
    if test_read_access(instance, access_property, any_match=lambda access: access[:9] == 'subgroup:'):
        return 2
    if test_read_access(instance, access_property, any_match=lambda access: access[:5] == 'user:'):
        return 1
    return 6


def test_read_access(instance, access_property, any_match):
    for access in getattr(instance, access_property):
        if any_match(access):
            return True
    return False

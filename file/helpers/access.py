def test_read_access(instance, any_match):
    for access in instance.read_access:
        if any_match(access):
            return True
    return False


def get_read_access_weight(instance):
    """ #1: Eigenaar
        #2: Subgroep
        #3: Groep
        #4: Ingelogd
        #5: Publiek
    """

    if test_read_access(instance, any_match=lambda access: access == 'public'):
        return 5
    if test_read_access(instance, any_match=lambda access: access == 'logged_in'):
        return 4
    if test_read_access(instance, any_match=lambda access: access[:6] == 'group:'):
        return 3
    if test_read_access(instance, any_match=lambda access: access[:9] == 'subgroup:'):
        return 2
    if test_read_access(instance, any_match=lambda access: access[:5] == 'user:'):
        return 1
    return 6

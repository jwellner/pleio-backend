def resolve_notifications(_, info, offset=0, limit=20, unread=None):
    """ Returns notification, which are created through methods in signals.py """
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    return {
        'offset': offset,
        'limit': limit,
        'unread': unread
    }

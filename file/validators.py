def valid_filename(value):
    return value and value[0] != '/'


def valid_mimetype(value):
    return value


def valid_filesize(value):
    return value > 0


def is_upload_complete(instance):
    try:
        if instance.upload:
            assert valid_filename(instance.title)
            assert valid_mimetype(instance.mime_type)
            assert valid_filesize(instance.size)
        return True
    except AssertionError:
        return False

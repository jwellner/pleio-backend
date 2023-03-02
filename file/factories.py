from core.constances import ACCESS_TYPE
from file.models import FileFolder
from user.models import User


def default_file(**attributes):
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return FileFolder.objects.create(**attributes)


def FileFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.FILE
    if kwargs.get('upload'):
        kwargs.setdefault('title', None)
    return default_file(**kwargs)


def FolderFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.FOLDER
    return default_file(**kwargs)


def PadFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.PAD
    return default_file(**kwargs)

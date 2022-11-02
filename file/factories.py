from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from file.models import FileFolder


def default_file(**kwargs):
    assert kwargs.get('owner'), "A file/folder/pad requires an owner."
    kwargs.setdefault('read_access', [ACCESS_TYPE.public])
    kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(kwargs['owner'].guid)])
    return mixer.blend(FileFolder, **kwargs)


def FileFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.FILE
    return default_file(**kwargs)


def FolderFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.FOLDER
    return default_file(**kwargs)


def PadFactory(**kwargs) -> FileFolder:
    kwargs['type'] = FileFolder.Types.PAD
    return default_file(**kwargs)

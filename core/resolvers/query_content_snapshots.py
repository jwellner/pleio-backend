from core.resolvers.shared import assert_authenticated
from file.models import FileFolder


def resolve_content_snapshots(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user
    assert_authenticated(user)

    return {
        'success': True,
        'edges': FileFolder.objects.content_snapshots(user=user)
    }

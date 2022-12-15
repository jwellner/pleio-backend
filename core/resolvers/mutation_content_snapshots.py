from core.lib import tenant_schema
from core.resolvers.query_content_snapshots import resolve_content_snapshots
from core.resolvers.shared import assert_authenticated


def resolve_create_content_snapshot(obj, info):
    user = info.context["request"].user

    assert_authenticated(user)

    from core.tasks.exports import export_my_content
    export_my_content.delay(tenant_schema(), user.guid)

    return resolve_content_snapshots(obj, info)

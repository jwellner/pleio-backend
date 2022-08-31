from django.utils.timezone import localtime, timedelta

from core.lib import tenant_schema
from core.models import AvatarExport
from core.resolvers import shared


def resolve_export_avatars(_, info):
    from core.tasks import export_avatars
    user = info.context["request"].user

    shared.assert_authenticated(user)
    shared.assert_administrator(user)

    threshold = localtime() - timedelta(hours=1)
    exists = AvatarExport.objects.filter(initiator=user, created_at__gt=threshold).exclude(status='ready')
    if exists:
        export = exists.first()
    else:
        export = AvatarExport.objects.create(initiator=user)
        export_avatars.delay(tenant_schema(), export.guid)

    return {
        'guid': export.guid,
        'status': export.status,
    }

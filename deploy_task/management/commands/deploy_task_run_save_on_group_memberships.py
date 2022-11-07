from core.models import GroupMembership
from deploy_task.utils import DeployCommandBase


def migrate_memberships():
    for membership in GroupMembership.objects.all():
        membership.save()


class Command(DeployCommandBase):
    deploy_task = migrate_memberships

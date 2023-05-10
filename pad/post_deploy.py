from post_deploy import post_deploy_action

from core.lib import is_schema_public
from core.resolvers import shared
from file.models import FileFolder


@post_deploy_action
def create_initial_revisions_for_existing_pads():
    if is_schema_public():
        return

    for file in FileFolder.objects.filter_pads():
        if not file.revision_set.exists() and file.has_revisions():
            shared.store_initial_revision(file)

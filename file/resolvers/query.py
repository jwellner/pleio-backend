from ariadne import ObjectType
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group, Entity
from file.models import FileFolder
from user.models import User
from django.db.models import Q

query = ObjectType("Query")


def conditional_group_folder_user_container_filter(container_guid, is_folder, is_user):
    if container_guid and not is_folder and not is_user:
        return Q(Q(group__id=container_guid) & Q(parent=None))

    if container_guid and is_folder:
        return Q(parent__id=container_guid)

    if container_guid and is_user:
        return Q(Q(owner__id=container_guid) & Q(parent=None) & Q(group=None))

    return Q()

def conditional_filter_subtype(subtype):

    if subtype == "files":
        return Q(is_folder=False)

    if subtype == "folders":
        return Q(is_folder=True)

    return Q()

@query.field("files")
def resolve_files(
        _,
        info,
        filter="all",
        containerGuid=None,
        offset=0,
        limit=20,
        orderBy="title",
        orderDirection="asc"
    ):
    #pylint: disable=unused-argument
    #pylint: disable=too-many-arguments
    #pylint: disable=redefined-builtin

    if orderBy == 'timeUpdated':
        order_by = 'updated_at'
    elif orderBy == 'timeCreated':
        order_by = 'published'
    else:
        order_by = 'title'

    if orderDirection == 'desc':
        order_by = '-%s' % (order_by)

    is_folder = False
    is_user = False

    # check if containerGuid is group, folder or user
    if containerGuid:
        try:
            Group.objects.get(id=containerGuid)
        except ObjectDoesNotExist:
            try:
                FileFolder.objects.get_subclass(id=containerGuid)
                is_folder = True
            except ObjectDoesNotExist:
                try:
                    User.objects.get(id=containerGuid)
                    is_user = True
                except ObjectDoesNotExist:
                    raise GraphQLError("INVALID_CONTAINER_GUID")

    qs = FileFolder.objects.visible(info.context["request"].user)
    qs = qs.filter(conditional_group_folder_user_container_filter(containerGuid, is_folder, is_user) & conditional_filter_subtype(filter))
    qs = qs.order_by('-is_folder', order_by)

    edges = qs[offset:offset+limit]

    return {
        'total': qs.count(),
        'edges': edges
    }

@query.field("breadcrumb")
def resolve_breadcrumb(_, info, guid):
    #pylint: disable=unused-argument
    path = []

    entity = None

    try:
        entity = Entity.objects.get_subclass(id=guid)
    except ObjectDoesNotExist:
        pass

    if entity:
        path.append(entity)
        if entity.parent:
            parent = entity.parent
            while parent:
                path.append(parent)
                parent = parent.parent

    path.reverse()

    return path

from core.constances import ACCESS_TYPE
from django.apps import apps
from enum import Enum

class TypeModels(Enum):
    """Can be used to convert GraphQL types to Django models"""

    news = "news.News"
    poll = "poll.Poll"
    discussion = "discussion.Discussion"
    event = "event.Event"
    wiki = "wiki.Wiki"
    question = "question.Question"
    page = "cms.CmsPage"
    blog = "blog.Blog"
    group = "core.Group"
    user = "core.User"
    

def get_model_by_subtype(subtype):
    """Get Django model by subtype name"""

    if TypeModels[subtype]:
        model_name = TypeModels[subtype].value
        return apps.get_model(model_name)
    
    return None

def access_id_to_acl(obj, access_id):

    acl = [ACCESS_TYPE.user.format(obj.owner.id)] # owner can always read

    if access_id == 1:
        acl.append(ACCESS_TYPE.logged_in)
    elif access_id == 2:
        acl.append(ACCESS_TYPE.public)
    elif obj.group and access_id == 4:
        acl.append(ACCESS_TYPE.group.format(obj.group.id))

    return acl

def resolve_entity_access_id(obj, info):
    # pylint: disable=unused-argument
    if obj.group and ACCESS_TYPE.group.format(obj.group.id) in obj.read_access:
        return 4
    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0

def resolve_entity_write_access_id(obj, info):
    # pylint: disable=unused-argument

    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0

def resolve_entity_can_edit(obj, info):
    return obj.can_write(info.context.user)

def resolve_entity_featured(obj, info):
    # pylint: disable=unused-argument

    if obj.featured_image:
        image = obj.featured_image.upload.url
    else:
        image = None

    return {
        'image': image,
        'video': obj.featured_video,
        'positionY': obj.featured_position_y
    }

from django.db.models import Q
from django.db.models.functions import Coalesce
from core.constances import ORDER_DIRECTION, ORDER_BY, INVALID_SUBTYPE
from core.models import Entity
from graphql import GraphQLError


def conditional_subtypes_filter(subtypes):
    """
    Filter multiple subtypes
    """
    q_objects = Q()
    if subtypes:
        for object_type in subtypes:
            if object_type == 'news':
                q_objects.add(~Q(news__isnull = True), Q.OR)
            elif object_type == 'blog':
                q_objects.add(~Q(blog__isnull = True), Q.OR)
            elif object_type == 'event':
                q_objects.add(~Q(event__isnull = True), Q.OR)
            elif object_type == 'discussion':
                q_objects.add(~Q(discussion__isnull = True), Q.OR)
            elif object_type == 'statusupdate':
                q_objects.add(~Q(statusupdate__isnull = True), Q.OR)
            elif object_type == 'question':
                q_objects.add(~Q(question__isnull = True), Q.OR)
            elif object_type == 'poll':
                q_objects.add(~Q(poll__isnull = True), Q.OR)
            elif object_type == 'wiki':
                q_objects.add(~Q(wiki__isnull = True), Q.OR)
            elif object_type == 'page':
                q_objects.add(~Q(page__isnull = True), Q.OR)
            elif object_type == 'file':
                q_objects.add(~Q(filefolder__isnull = True), Q.OR)
            elif object_type == 'task':
                q_objects.add(~Q(task__isnull = True), Q.OR)

    return q_objects

def conditional_group_filter(container_guid):
    """
    Filter only items in group
    """
    if container_guid == "1":
        return Q(group=None)
    if container_guid:
        return Q(group__id=container_guid)

    return Q()

def conditional_is_featured_filter(is_featured):
    """
    Only filter is_featured on news list
    """
    q_objects = Q()
    if is_featured:
        q_objects.add(Q(blog__is_featured = True), Q.OR)
        q_objects.add(Q(news__is_featured = True), Q.OR)
        q_objects.add(Q(event__is_featured = True), Q.OR)
        q_objects.add(Q(question__is_featured = True), Q.OR)
        q_objects.add(Q(discussion__is_featured = True), Q.OR)
        q_objects.add(Q(wiki__is_featured = True), Q.OR)

    return q_objects

def conditional_tags_filter(tags):
    if tags:
        filters = Q()
        for tag in tags:
            filters.add(Q(tags__overlap=[tag]), Q.AND) # of Q.OR

        return filters
    return Q()

def conditional_tag_lists_filter(tag_lists):
    filters = Q()
    if tag_lists:
        for tags in tag_lists:
            if tags:
                filters.add(Q(tags__overlap=tags), Q.AND) # of Q.OR
    return filters

def resolve_entities(
    _,
    info,
    offset=0,
    limit=20,
    type=None,
    subtype=None,
    subtypes=None,
    containerGuid=None,
    tags=None,
    tagLists=None,
    orderBy=ORDER_BY.timePublished,
    orderDirection=ORDER_DIRECTION.desc,
    isFeatured=None,
    sortPinned=False,
    isDraft=False,
    userGuid=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches

    # merge all in subtypes list
    if not subtypes and subtype:
        subtypes = [subtype]
    elif not subtypes and not subtype:
        subtypes = []

    Model = Entity

    if not Model:
        raise GraphQLError(INVALID_SUBTYPE)

    if orderBy == ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    if orderBy == ORDER_BY.timeCreated:
        order_by = 'created_at'
    elif orderBy == ORDER_BY.lastAction:
        order_by = 'last_action'
    elif orderBy == ORDER_BY.title:
        order_by = 'title'
    else:
        order_by = 'published'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    if order_by == '-title':
        order_by = Coalesce('news__title', 'blog__title', 'filefolder__title', 'poll__title', 'statusupdate__title', 'wiki__title',
                                              'page__title', 'question__title', 'discussion__title', 'event__title').desc()
    elif order_by == 'title':
        order_by = Coalesce('news__title', 'blog__title', 'filefolder__title', 'poll__title', 'statusupdate__title', 'wiki__title',
                                              'page__title', 'question__title', 'discussion__title', 'event__title').asc()

    if isDraft:
        entities = Model.objects.draft(info.context["request"].user)
    else:
        entities = Model.objects.visible(info.context["request"].user)

    entities = entities.filter(conditional_group_filter(containerGuid) &
                               conditional_tags_filter(tags) &
                               conditional_tag_lists_filter(tagLists) &
                               conditional_subtypes_filter(subtypes) &
                               conditional_is_featured_filter(isFeatured))

    if userGuid:
        entities = entities.filter(owner__id=userGuid)

    # when page is selected change sorting and only return pages without parent
    if subtype and subtype == 'page':
        entities = entities.filter(page__parent=None)
        order_by = 'page__title'

    # only return wiki's without parent
    if subtype and subtype == 'wiki':
        entities = entities.filter(wiki__parent=None)

    order = [order_by]

    if sortPinned:
        order = ["-is_pinned"] + order

    entities = entities.order_by(*order).select_subclasses()

    edges = entities[offset:offset+limit]

    return {
        'total': entities.count(),
        'edges': edges,
    }

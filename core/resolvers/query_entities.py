import logging

from django.db.models import Q, F
from django.db.models.functions import Coalesce, Lower
from core.constances import (ORDER_DIRECTION, ORDER_BY, INVALID_SUBTYPE,
                             COULD_NOT_ORDER_BY_START_DATE, COULD_NOT_USE_EVENT_FILTER)
from core.lib import early_this_morning
from core.models import Entity
from graphql import GraphQLError

from core.models.tags import Tag, flat_category_tags

logger = logging.getLogger(__name__)


def conditional_subtypes_filter(subtypes):
    """
    Filter multiple subtypes
    """
    q_objects = Q()
    if subtypes:
        for object_type in subtypes:
            if object_type == 'news':
                q_objects.add(~Q(news__isnull=True), Q.OR)
            elif object_type == 'blog':
                q_objects.add(~Q(blog__isnull=True), Q.OR)
            elif object_type == 'event':
                q_objects.add(~Q(event__isnull=True) & ~Q(event__parent__isnull=False), Q.OR)
            elif object_type == 'discussion':
                q_objects.add(~Q(discussion__isnull=True), Q.OR)
            elif object_type == 'statusupdate':
                q_objects.add(~Q(statusupdate__isnull=True), Q.OR)
            elif object_type == 'question':
                q_objects.add(~Q(question__isnull=True), Q.OR)
            elif object_type == 'poll':
                q_objects.add(~Q(poll__isnull=True), Q.OR)
            elif object_type == 'wiki':
                q_objects.add(~Q(wiki__isnull=True), Q.OR)
            elif object_type == 'page':
                q_objects.add(~Q(page__isnull=True), Q.OR)
            elif object_type == 'file':
                q_objects.add(~Q(filefolder__isnull=True), Q.OR)
            elif object_type == 'task':
                q_objects.add(~Q(task__isnull=True), Q.OR)
    else:
        q_objects.add(~Q(news__isnull=True), Q.OR)
        q_objects.add(~Q(blog__isnull=True), Q.OR)
        q_objects.add(~Q(event__isnull=True) & ~Q(event__parent__isnull=False), Q.OR)
        q_objects.add(~Q(discussion__isnull=True), Q.OR)
        q_objects.add(~Q(statusupdate__isnull=True), Q.OR)
        q_objects.add(~Q(question__isnull=True), Q.OR)
        q_objects.add(~Q(poll__isnull=True), Q.OR)
        q_objects.add(~Q(wiki__isnull=True), Q.OR)
        q_objects.add(~Q(page__isnull=True), Q.OR)
        q_objects.add(~Q(filefolder__isnull=True), Q.OR)
        q_objects.add(~Q(task__isnull=True), Q.OR)
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
    if is_featured:
        return Q(is_featured=True)

    return Q()


def conditional_tags_filter(tags, match_any):
    if tags:
        filters = Q()
        if match_any:
            filters.add(Q(_tag_summary__overlap=Tag.translate_tags(tags)), Q.AND)
        else:
            for tag in Tag.translate_tags(tags):
                filters.add(Q(_tag_summary__overlap=[tag]), Q.AND)  # of Q.OR

        return filters
    return Q()


def conditional_tag_lists_filter(categorytag_lists, match_any):
    filters = Q()
    if categorytag_lists:
        for category in categorytag_lists:
            if category:
                matches = flat_category_tags(category)
                if match_any:
                    filters.add(Q(_category_summary__overlap=matches), Q.AND)
                else:
                    for match in matches:
                        filters.add(Q(_category_summary__overlap=[match]), Q.AND)
    return filters


def conditional_event_filter(date_filter):
    if date_filter == 'previous':
        return Q(event__start_date__lt=early_this_morning())
    return Q(event__start_date__gte=early_this_morning())


def resolve_entities(
        _,
        info,
        offset=0,
        limit=20,
        type=None,
        subtype=None,
        subtypes=None,
        containerGuid=None,
        eventFilter=None,
        tags=None,
        tagCategories=None,
        matchStrategy='any',
        orderBy=ORDER_BY.timePublished,
        orderDirection=ORDER_DIRECTION.desc,
        isFeatured=None,
        sortPinned=False,
        statusPublished=None,
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
        order_by = 'sort_title'
    elif orderBy == ORDER_BY.startDate:
        if subtypes == ['event']:
            order_by = 'event__start_date'
        else:
            raise GraphQLError(COULD_NOT_ORDER_BY_START_DATE)
    else:
        order_by = 'published'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    if statusPublished and len(statusPublished) > 0:
        entities = Model.objects.status_published(statusPublished, info.context["request"].user)
    else:
        entities = Model.objects.visible(info.context["request"].user)

    entities = entities.filter(conditional_is_featured_filter(isFeatured) &
                               conditional_group_filter(containerGuid) &
                               conditional_subtypes_filter(subtypes) &
                               conditional_tags_filter(tags, matchStrategy == 'any') &
                               conditional_tag_lists_filter(tagCategories, matchStrategy != 'all'))

    if userGuid:
        entities = entities.filter(owner__id=userGuid)

    if eventFilter:
        if subtypes == ['event']:
            entities = entities.filter(conditional_event_filter(eventFilter))
        else:
            raise GraphQLError(COULD_NOT_USE_EVENT_FILTER)

    # when page is selected change sorting and only return pages without parent
    if subtype and subtype == 'page':
        entities = entities.filter(page__parent=None)
        entities = entities.annotate(sort_title=Lower("page__title"))
        order_by = 'sort_title'

    # only return wiki's without parent
    elif subtype and subtype == 'wiki':
        entities = entities.filter(wiki__parent=None)
        entities = entities.annotate(sort_title=Lower("wiki__title"))

    else:
        entities = entities.annotate(sort_title=Lower(Coalesce('news__title',
                                                               'blog__title',
                                                               'filefolder__title',
                                                               'poll__title',
                                                               'statusupdate__title',
                                                               'wiki__title',
                                                               'page__title',
                                                               'question__title',
                                                               'discussion__title',
                                                               'event__title')))

    order = [order_by]

    if sortPinned:
        order = ["-is_pinned"] + order

    entities = entities.order_by(*order).select_subclasses()

    edges = entities[offset:offset + limit]

    return {
        'total': entities.count(),
        'edges': edges,
    }

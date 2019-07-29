from ariadne import ObjectType
from core.models import Object
from django.db.models import Q

query = ObjectType("Query")


def conditional_subtypes_filter(subtypes):
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

    return q_objects

def conditional_tags_filter(tags):
    if tags:
        return Q(tags__contains=tags)

    return Q()

@query.field("activities")
def resolve_activities(
        _,
        info,
        containerGuid=None,
        offset=0,
        limit=20,
        tags=None,
        groupFilter=None,
        subtypes=None,
        orderBy="timeCreated",
        orderDirection="desc"
    ):
    #pylint: disable=unused-argument
    #pylint: disable=too-many-arguments

    # TODO: how to do lastAction?
    if orderBy == 'timeUpdated':
        order_by = 'updated_at'
    elif orderBy == 'lastAction':
        order_by = 'updated_at'
    else:
        order_by = 'created_at'
    
    if orderDirection == 'desc':
        order_by = '-%s' % (order_by)
   
    qs = Object.objects
    qs = qs.filter(conditional_subtypes_filter(subtypes) & conditional_tags_filter(tags))
    qs = qs.order_by(order_by).select_subclasses()
    total = qs.count()

    qs = qs[offset:offset+limit]

    activities = []

    for item in qs :
        
        activity = {
            'guid': 'activity:%s' % (item.guid),
            'type': 'create',
            'entity': item 
        }

        activities.append(activity)

    return {
        'total': total,
        'edges': activities
    }


resolvers = [query]

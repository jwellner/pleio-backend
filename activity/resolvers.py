from ariadne import ObjectType
from actstream.models import Action

query = ObjectType("Query")


@query.field("activities")
def resolve_activities(_, info, containerGuid=None, offset=0, limit=20, tags=None, groupFilter=None, subtypes=None, orderBy=None, orderDirection=None):
    #pylint: disable=unused-argument
    #pylint: disable=too-many-arguments

    data = Action.objects.filter(public=True)[0:limit]

    edges = []

    for item in data :

        if item.verb == 'updated' :
            activity_type = 'update'
        elif item.verb == 'created': 
            activity_type = 'create'
        
        activity = {
            'guid': 'activity:%i' % (item.id),
            'type': activity_type,
            'entity': item.target 
        }

        edges.append(activity)

    return {
        'total': len(edges),
        'edges': edges
    }


resolvers = [query]

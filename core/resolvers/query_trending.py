from collections import Counter
from core.models import Entity, Annotation


def resolve_trending(_, info):
    """ Return trending tags

    - Get the last 250 content items voted on
    - Add the tags of these items to a list 

    Return tags with 3 most occurences
    """
    # TODO: filter entity objects
    # pylint: disable=unused-argument
    entity_tags = {}
    total_tags = []
    trending_tags = []

    voted_object_ids = Annotation.objects.filter(key='voted')[0:250].values_list('object_id', flat=True)

    entities = Entity.objects.filter(id__in=voted_object_ids).values('id', 'tags')

    # Create list with dictionaries: [{'id': [tags]}]
    for entity in entities:
        entity_tags[entity['id']] = entity['tags']

    # Add all tag lists to a list
    for object_id in voted_object_ids:
        if object_id in entity_tags:
            total_tags.append(entity_tags[object_id])

    # Count all occurences in total_tags of a tag and get 3 most ocurring tags with count
    most_ocurring_tags = Counter(x for xs in total_tags for x in set(xs)).most_common(3)

    for tag, likes in most_ocurring_tags:
        trending_tags.append({'tag': tag, 'likes': likes})

    return trending_tags

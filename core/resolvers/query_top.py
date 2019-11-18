from collections import Counter
from core.models import Entity, Annotation

def resolve_top(_, info):
    # pylint: disable=unused-argument
    entity_owners = {}
    total_owners = []
    top_users = []

    voted_object_ids = Annotation.objects.filter(key='voted')[0:250].values_list('object_id', flat=True)

    entities = Entity.objects.filter(id__in=voted_object_ids)

    # Create list with dictionaries: [{'id': [tags]}]
    for entity in entities:
        entity_owners[entity.id] = entity.owner

    # Add all tag lists to a list
    for object_id in voted_object_ids:
        if object_id in entity_owners:
            total_owners.append(entity_owners[object_id])

    # Count all occurences in total_tags of a tag and get 3 most ocurring tags with count
    most_ocurring_users = Counter(total_owners).most_common(3)

    # print(most_ocurring_users)
    for user, likes in most_ocurring_users:
        top_users.append({'user': user, 'likes': likes})

    return top_users

from core.models.tags import Tag


def resolve_list_tags(obj, info):
    # pylint: disable=unused-argument
    return [
        {'label': t.label,
         'synonyms': [s.label for s in t.synonyms.all()]
         } for t in Tag.objects.all()
    ]

from core.lib import get_model_by_subtype


def resolve_recommended(
    _,
    info,
    offset=0,
    limit=20
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    Model = get_model_by_subtype('blog')
    entities = Model.objects.visible(info.context["request"].user)
    entities = entities.filter(is_recommended=True)

    edges = entities[offset:offset+limit]

    return {
        'total': entities.count(),
        'edges': edges,
    }

class EntityNotFoundError(Exception):
    pass


def load_entity_by_id(guid, class_references=None):
    for class_reference in class_references:
        if class_reference.objects.filter(id=guid).exists():
            return maybe_subclass(class_reference.objects.filter(id=guid))

    raise EntityNotFoundError("Not an entity GUID")


def maybe_subclass(qs):
    try:
        return qs.select_subclasses().first()
    except AttributeError:
        return qs.first()

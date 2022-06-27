class EntityNotFoundError(Exception):
    pass


def load_entity_by_id(guid, class_references=None, fail_if_not_found=True):
    for class_reference in translate_models(class_references):
        if class_reference.objects.filter(id=guid).exists():
            return maybe_subclass(class_reference.objects.filter(id=guid))
    if fail_if_not_found:
        raise EntityNotFoundError("Not an entity GUID")
    return None


def maybe_subclass(qs):
    try:
        return qs.select_subclasses().first()
    except AttributeError:
        return qs.first()


def translate_models(class_references):
    from django.apps import apps
    for reference in class_references:
        if isinstance(reference, (str,)):
            yield apps.get_model(reference)
        else:
            yield reference

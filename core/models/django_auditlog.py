from auditlog.models import LogEntryManager, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_str

# Monkey patch django auditlog LogEntryManager.log_create and remove self.using(db).create

def log_create(self, instance, **kwargs):
    # pylint: disable=protected-access
    """
    Helper method to create a new log entry. This method automatically populates some fields when no explicit value
    is given.
    :param instance: The model instance to log a change for.
    :type instance: Model
    :param kwargs: Field overrides for the :py:class:`LogEntry` object.
    :return: The new log entry or `None` if there were no changes.
    :rtype: LogEntry
    """
    changes = kwargs.get("changes", None)
    pk = self._get_pk_value(instance)

    if changes is not None:
        kwargs.setdefault(
            "content_type", ContentType.objects.get_for_model(instance)
        )
        kwargs.setdefault("object_pk", pk)
        kwargs.setdefault("object_repr", smart_str(instance))

        if isinstance(pk, int):
            kwargs.setdefault("object_id", pk)

        get_additional_data = getattr(instance, "get_additional_data", None)
        if callable(get_additional_data):
            kwargs.setdefault("additional_data", get_additional_data())

        # Delete log entries with the same pk as a newly created model. This should only be necessary when an pk is
        # used twice.
        if kwargs.get("action", None) is LogEntry.Action.CREATE:
            if (
                kwargs.get("object_id", None) is not None
                and self.filter(
                    content_type=kwargs.get("content_type"),
                    object_id=kwargs.get("object_id"),
                ).exists()
            ):
                self.filter(
                    content_type=kwargs.get("content_type"),
                    object_id=kwargs.get("object_id"),
                ).delete()
            else:
                self.filter(
                    content_type=kwargs.get("content_type"),
                    object_pk=kwargs.get("object_pk", ""),
                ).delete()

        return (
            self.create(**kwargs)
        )
    return None


LogEntryManager.log_create = log_create
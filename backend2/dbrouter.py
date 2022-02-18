from django.conf import settings
import random

class PrimaryReplicaRouter:

    def __init__(self):
        self.has_replica = bool(settings.DATABASES.get("replica", False))

    def db_for_read(self, model, **hints):
        # pylint: disable=unused-argument
        """
        Reads go to a randomly-chosen replica or primary.
        """
        return random.choice(['default', 'replica']) if self.has_replica else 'default'

    def db_for_write(self, model, **hints):
        # pylint: disable=unused-argument
        """
        Writes always go to primary.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # pylint: disable=unused-argument
        # pylint: disable=protected-access
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # pylint: disable=unused-argument
        """
        All non-auth models end up in this pool.
        """
        return True
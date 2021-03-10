import uuid
from django.db import models

class FlowId(models.Model):

    flow_id = models.IntegerField(unique=True, editable=False)
    object_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

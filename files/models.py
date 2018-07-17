import uuid
import os
import time
from django.db import models
from core.models import User

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('binary_file', time.strftime('%Y/%m/%d'), filename)

class BinaryFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    content_type = models.CharField(max_length=200)
    size = models.BigIntegerField(default=0)
    file = models.FileField(upload_to=get_file_path)
    created_at = models.DateTimeField(auto_now_add=True)

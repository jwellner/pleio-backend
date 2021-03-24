from django.db import models

class Logs(models.Model):

    uuid = models.CharField(max_length=36)
    content = models.TextField()

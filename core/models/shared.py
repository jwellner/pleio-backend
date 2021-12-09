import abc
from django.db import models

def read_access_default():
    return []


def write_access_default():
    return []

class AbstractModelMeta(abc.ABCMeta, type(models.Model)):
    pass

from importlib import import_module
import inspect

import graphene
from django.apps import apps

def get_queries_from_apps(module_name='query'):
    queries = []
    for app in apps.get_app_configs():
        try:
            modentry = "%s.%s" % (app.name, module_name)
            mod = import_module(modentry)
            clsmembers = inspect.getmembers(mod, inspect.isclass)
            clsmembers = [i for i, k in inspect.getmembers(mod, inspect.isclass) if k.__module__ == modentry]
            for i in clsmembers:
                try:
                    cls = getattr(mod, i)
                    queries.append(cls)
                except AttributeError:
                    pass
        except ModuleNotFoundError:
            pass
    return tuple(queries)

def get_mutations_from_apps(module_name='mutation'):
    mutations = []
    for app in apps.get_app_configs():
        try:
            modentry = "%s.%s" % (app.name, module_name)
            mod = import_module(modentry)
            clsmembers = inspect.getmembers(mod, inspect.isclass)
            clsmembers = [i for i, k in inspect.getmembers(mod, inspect.isclass) if k.__module__ == modentry]
            for i in clsmembers:
                try:
                    cls = getattr(mod, i)
                    if graphene.ObjectType in cls.__bases__:
                        mutations.append(cls)
                except AttributeError:
                    pass
        except ModuleNotFoundError:
            pass
    return tuple(mutations)

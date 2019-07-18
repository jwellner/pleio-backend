from importlib import import_module
from django.apps import apps

from ariadne import load_schema_from_path, make_executable_schema

# load schema from file...
type_defs = load_schema_from_path("backend2/schema.graphql")

# get resolvers form apps
resolvers = []
for app in apps.get_app_configs():
    try:
        search = "%s.%s" % (app.name, "resolvers")
        app_module = import_module(search)
        app_resolvers = getattr(app_module, "resolvers")
        resolvers.extend(app_resolvers)
        print("Loaded resolver: %s" % app.name)
    except ImportError as e:
        print(e)


schema = make_executable_schema(type_defs, resolvers)

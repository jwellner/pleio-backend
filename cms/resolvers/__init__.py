from ariadne import ObjectType, InterfaceType
from .page import page
from .mutation import mutation
from .row import row

resolvers = [page, mutation, row]

from ariadne import ObjectType, InterfaceType
from .page import page
from .mutation import mutation
from .row import row
from .column import column

resolvers = [page, mutation, row, column]

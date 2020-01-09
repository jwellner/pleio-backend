from ariadne import ObjectType, InterfaceType
from .page import page
from .mutation import mutation

resolvers = [page, mutation]

from ariadne import ObjectType, InterfaceType
from .mutation import mutation
from .query import query
from .user import user
from .group import group
from .member import member
from .viewer import viewer
from .entity import entity


resolvers = [query, mutation, viewer, entity, user, group, member]

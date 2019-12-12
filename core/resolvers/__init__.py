from ariadne import ObjectType, InterfaceType
from .mutation import mutation
from .query import query
from .user import user
from .group import group
from .member import member
from .viewer import viewer
from .entity import entity
from .comment import comment
from .profile_item import profile_item
from .widget import widget
from .invite import invite

resolvers = [query, mutation, viewer, entity, user, group, member, comment, profile_item, widget, invite]

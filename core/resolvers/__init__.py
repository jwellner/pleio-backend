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
from .subgroup_list import subgroup_list
from .subgroup import subgroup
from .email_overview import email_overview
from .notification import notification
from .notifications_list import notifications_list
from .site import site
from .profile_field_validator import profile_field_validator
from .attachment import attachment
from .filters import filters

resolvers = [
    query, mutation, viewer, entity, user, group, member, comment, profile_item,
    profile_field_validator, widget, invite, subgroup_list, subgroup, email_overview,
    notification, site, attachment, notifications_list, filters
]
from .mutation import mutation
from .query import query
from .user import user
from .group import group
from .member import member
from .viewer import viewer
from .entity import entity
from .comment import comment
from .profile_item import profile_item
from .invite import invite
from .subgroup_list import subgroup_list
from .subgroup import subgroup
from .email_overview import email_overview
from .notification import notification
from .notifications_list import notifications_list
from .site_agreement import site_agreement
from .site_agreement_version import site_agreement_version
from .profile_field_validator import profile_field_validator
from .attachment import attachment
from .filters import filters
from .revision import revision, content_version
from .scalar import secure_rich_text
from .site_settings import site_settings_private, site_settings_public

resolvers = [
    query, mutation, viewer, entity, user, group, member, comment, profile_item,
    profile_field_validator, invite, subgroup_list, subgroup, email_overview,
    notification, attachment, notifications_list, filters, revision, content_version,
    secure_rich_text, site_agreement, site_agreement_version, site_settings_private, site_settings_public
]

from ariadne import ObjectType

from core.resolvers.mutation_archive_entity import resolve_archive_entity
from .mutation_add_group import resolve_add_group
from .mutation_edit_group import resolve_edit_group
from .mutation_join_group import resolve_join_group
from .mutation_leave_group import resolve_leave_group
from .mutation_invite_to_group import resolve_invite_to_group
from .mutation_accept_group_invitation import resolve_accept_group_invitation
from .mutation_resend_group_invitation import resolve_resend_group_invitation
from .mutation_delete_group_invitation import resolve_delete_group_invitation
from .mutation_change_group_role import resolve_change_group_role
from .mutation_send_message_to_group import resolve_send_message_to_group
from .mutation_accept_membership_request import resolve_accept_membership_request
from .mutation_reject_membership_request import resolve_reject_membership_request
from .mutation_add_subgroup import resolve_add_subgroup
from .mutation_edit_subgroup import resolve_edit_subgroup
from .mutation_delete_subgroup import resolve_delete_subgroup
from .mutation_add_group_widget import resolve_add_group_widget
from .mutation_edit_group_widget import resolve_edit_group_widget
from .mutation_add_entity import resolve_add_entity
from .mutation_edit_entity import resolve_edit_entity
from .mutation_copy_entity import resolve_copy_entity
from .mutation_delete_entity import resolve_delete_entity
from .mutation_delete_user import resolve_delete_user
from .mutation_tags import resolve_merge_tags, resolve_extract_tag_synonym
from .mutation_toggle_user_role import resolve_toggle_user_role
from .mutation_toggle_user_is_banned import resolve_toggle_user_is_banned
from .mutation_edit_users import resolve_edit_users
from .mutation_vote import resolve_vote
from .mutation_bookmark import resolve_bookmark
from .mutation_follow import resolve_follow
from .mutation_send_message_to_user import resolve_send_message_to_user
from .mutation_toggle_request_delete_user import resolve_toggle_request_delete_user
from .mutation_mark_as_read import resolve_mark_as_read, resolve_mark_all_as_read
from .mutation_edit_email_overview import resolve_edit_email_overview
from .mutation_edit_notifications import resolve_edit_notifications
from .mutation_edit_group_notifications import resolve_edit_group_notifications
from .mutation_edit_profile_field import resolve_edit_profile_field
from .mutation_reorder import resolve_reorder
from .mutation_edit_site_setting import resolve_edit_site_setting
from .mutation_add_site_setting_profile_field import resolve_add_site_setting_profile_field
from .mutation_edit_site_setting_profile_field import resolve_edit_site_setting_profile_field
from .mutation_delete_site_setting_profile_field import resolve_delete_site_setting_profile_field
from .mutation_invite_to_site import resolve_invite_to_site
from .mutation_revoke_invite_to_site import resolve_revoke_invite_to_site
from .mutation_handle_site_access_request import resolve_handle_site_access_request
from .mutation_handle_delete_account_request import resolve_handle_delete_account_request
from .mutation_import_users import resolve_import_users_step_1, resolve_import_users_step_2
from .mutation_add_site_setting_profile_field_validator import resolve_add_site_setting_profile_field_validator
from .mutation_edit_site_setting_profile_field_validator import resolve_edit_site_setting_profile_field_validator
from .mutation_delete_site_setting_profile_field_validator import resolve_delete_site_setting_profile_field_validator
from .mutation_add_attachment import resolve_add_attachment
from .mutation_toggle_entity_is_pinned import resolve_toggle_entity_is_pinned
from .mutation_edit_user_name import resolve_edit_user_name
from .mutation_add_comment_without_account import resolve_add_comment_without_account
from .mutation_sign_site_agreement_version import resolve_sign_site_agreement_version

mutation = ObjectType("Mutation")
mutation.set_field("addGroup", resolve_add_group)
mutation.set_field("editGroup", resolve_edit_group)
mutation.set_field("joinGroup", resolve_join_group)
mutation.set_field("leaveGroup", resolve_leave_group)
mutation.set_field("inviteToGroup", resolve_invite_to_group)
mutation.set_field("acceptGroupInvitation", resolve_accept_group_invitation)
mutation.set_field("resendGroupInvitation", resolve_resend_group_invitation)
mutation.set_field("deleteGroupInvitation", resolve_delete_group_invitation)
mutation.set_field("changeGroupRole", resolve_change_group_role)
mutation.set_field("sendMessageToGroup", resolve_send_message_to_group)
mutation.set_field("acceptMembershipRequest", resolve_accept_membership_request)
mutation.set_field("rejectMembershipRequest", resolve_reject_membership_request)
mutation.set_field("addSubgroup", resolve_add_subgroup)
mutation.set_field("editSubgroup", resolve_edit_subgroup)
mutation.set_field("deleteSubgroup", resolve_delete_subgroup)
mutation.set_field("addGroupWidget", resolve_add_group_widget)
mutation.set_field("editGroupWidget", resolve_edit_group_widget)

mutation.set_field("addEntity", resolve_add_entity)
mutation.set_field("editEntity", resolve_edit_entity)
mutation.set_field("copyEntity", resolve_copy_entity)
mutation.set_field("deleteEntity", resolve_delete_entity)
mutation.set_field("toggleEntityArchived", resolve_archive_entity)
mutation.set_field("deleteUser", resolve_delete_user)
mutation.set_field("toggleUserRole", resolve_toggle_user_role)
mutation.set_field("toggleUserIsBanned", resolve_toggle_user_is_banned)
mutation.set_field("editUsers", resolve_edit_users)

mutation.set_field("vote", resolve_vote)

mutation.set_field("bookmark", resolve_bookmark)
mutation.set_field("follow", resolve_follow)

mutation.set_field("sendMessageToUser", resolve_send_message_to_user)
mutation.set_field("toggleRequestDeleteUser", resolve_toggle_request_delete_user)

mutation.set_field("markAsRead", resolve_mark_as_read)
mutation.set_field("markAllAsRead", resolve_mark_all_as_read)

mutation.set_field("editEmailOverview", resolve_edit_email_overview)
mutation.set_field("editNotifications", resolve_edit_notifications)
mutation.set_field("editGroupNotifications", resolve_edit_group_notifications)

mutation.set_field("editProfileField", resolve_edit_profile_field)

mutation.set_field("reorder", resolve_reorder)

mutation.set_field("editSiteSetting", resolve_edit_site_setting)
mutation.set_field("editSiteSettingProfileField", resolve_edit_site_setting_profile_field)
mutation.set_field("addSiteSettingProfileField", resolve_add_site_setting_profile_field)
mutation.set_field("deleteSiteSettingProfileField", resolve_delete_site_setting_profile_field)

mutation.set_field("addSiteSettingProfileFieldValidator", resolve_add_site_setting_profile_field_validator)
mutation.set_field("editSiteSettingProfileFieldValidator", resolve_edit_site_setting_profile_field_validator)
mutation.set_field("deleteSiteSettingProfileFieldValidator", resolve_delete_site_setting_profile_field_validator)

mutation.set_field("inviteToSite", resolve_invite_to_site)
mutation.set_field("revokeInviteToSite", resolve_revoke_invite_to_site)

mutation.set_field("handleSiteAccessRequest", resolve_handle_site_access_request)
mutation.set_field("handleDeleteAccountRequest", resolve_handle_delete_account_request)
mutation.set_field("importUsersStep1", resolve_import_users_step_1)
mutation.set_field("importUsersStep2", resolve_import_users_step_2)

mutation.set_field("addAttachment", resolve_add_attachment)
mutation.set_field("toggleEntityIsPinned", resolve_toggle_entity_is_pinned)
mutation.set_field("editUserName", resolve_edit_user_name)
mutation.set_field("addCommentWithoutAccount", resolve_add_comment_without_account)

mutation.set_field("mergeTags", resolve_merge_tags)
mutation.set_field("extractTagSynonym", resolve_extract_tag_synonym)

mutation.set_field("signSiteAgreementVersion", resolve_sign_site_agreement_version)

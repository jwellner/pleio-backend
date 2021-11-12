ALREADY_MEMBER_OF_GROUP = "already_member_of_group"
ALREADY_REGISTERED = "already_registered"
ALREADY_VOTED = "already_voted"
COULD_NOT_ADD = "could_not_add"
COULD_NOT_DELETE = "could_not_delete"
COULD_NOT_FIND = "could_not_find"
COULD_NOT_CHANGE = "could_not_change"
COULD_NOT_FIND_GROUP = "could_not_find_group"
COULD_NOT_FIND_MEMBERSHIP_REQUEST = "could_not_find_membership_request"
COULD_NOT_FIND_USER = "could_not_find_user"
COULD_NOT_INVITE = "could_not_invite"
COULD_NOT_LEAVE = "could_not_leave"
COULD_NOT_LOGIN = "could_not_login"
COULD_NOT_LOGOUT = "could_not_logout"
COULD_NOT_REGISTER = "could_not_register"
COULD_NOT_SAVE = "could_not_save"
COULD_NOT_SEND = "could_not_send"
EMAIL_ALREADY_IN_USE = "email_already_in_use"
EMAIL_ALREADY_USED = "email_already_used"
INVALID_ANSWER = "invalid_answer"
INVALID_CODE = "invalid_code"
INVALID_EMAIL = "invalid_email"
INVALID_FILESIZE = "invalid_filesize"
INVALID_FILTER = "invalid_filter"
INVALID_KEY = "invalid_key"
INVALID_NEW_CONTAINER = "invalid_new_container"
INVALID_NEW_PASSWORD = "invalid_new_password"
INVALID_OBJECT_SUBTYPE = "invalid_object_subtype"
INVALID_OBJECT_TYPE = "invalid_object_type"
INVALID_OLD_PASSWORD = "invalid_old_password"
INVALID_PARENT = "invalid_parent"
INVALID_SUBTYPE = "invalid_subtype"
INVALID_TYPE = "invalid_type"
INVALID_VALUE = "invalid_value"
INVALID_DATE = "invalid_date"
INVALID_CONTENT_GUID = "invalid_content_guid"
KEY_ALREADY_IN_USE = "key_already_in_use"
LEAVING_GROUP_IS_DISABLED = "leaving_group_is_disabled"
NO_FILE = "no_file"
NOT_A_USER = "not_a_user"
NOT_LOGGED_IN = "not_logged_in"
NOT_MEMBER_OF_SITE = "not_member_of_site"
UNKNOWN_ERROR = "unknown_error"
USER_NOT_GROUP_OWNER_OR_SITE_ADMIN = "user_not_group_owner_or_site_admin"
USER_NOT_MEMBER_OF_GROUP = "user_not_member_of_group"
USER_NOT_SITE_ADMIN = "user_not_site_admin"
EVENT_IS_FULL = "event_is_full"
EVENT_INVALID_STATE = "event_invalid_state"
REDIRECTS_HAS_LOOP = "redirects_has_loop"
REDIRECTS_HAS_DUPLICATE_SOURCE = "redirects_has_duplicate_source"

class ORDER_DIRECTION:
    asc = 'asc'
    desc = 'desc'

class ORDER_BY:
    timeCreated = 'timeCreated'
    timeUpdated = 'timeUpdated'
    timePublished = 'timePublished'
    lastAction = 'lastAction'
    title = 'title'

class SEARCH_ORDER_BY:
    timeCreated = 'timeCreated'
    timePublished = 'timePublished'
    title = 'title'

class ACCESS_TYPE:
    logged_in = 'logged_in'
    public = 'public'
    user = 'user:{}'
    group = 'group:{}'
    subgroup = 'subgroup:{}'

class MEMBERSHIP:
    not_joined = 'not_joined'
    requested = 'requested'
    invited = 'invited'
    joined = 'joined'

class USER_ROLES:
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    QUESTION_MANAGER = "QUESTION_MANAGER"

class VISIBILITY:
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"

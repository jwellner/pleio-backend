from ariadne import ObjectType
from django.utils import timezone
from django.templatetags.static import static
from core import config
from core.models import UserProfile, ProfileField
from core.lib import get_access_ids, get_activity_filters

site = ObjectType("Site")

@site.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return 1

@site.field("name")
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return config.NAME

@site.field("theme")
def resolve_theme(obj, info):
    # pylint: disable=unused-argument
    return config.THEME

@site.field("menu")
def resolve_menu(obj, info):
    # pylint: disable=unused-argument
    return config.MENU

@site.field("profile")
def resolve_profile(obj, info):
    # pylint: disable=unused-argument
    return config.PROFILE

@site.field("profileSections")
def resolve_profile_sections(obj, info):
    # pylint: disable=unused-argument
    return config.PROFILE_SECTIONS

@site.field("footer")
def resolve_footer(obj, info):
    # pylint: disable=unused-argument
    return config.FOOTER

@site.field("directLinks")
def resolve_direct_links(obj, info):
    # pylint: disable=unused-argument
    return config.DIRECT_LINKS

@site.field("accessIds")
def resolve_access_ids(obj, info):
    # pylint: disable=unused-argument
    return get_access_ids()

@site.field("defaultAccessId")
def resolve_default_access_id(obj, info):
    # pylint: disable=unused-argument
    
    # Never return default access id 2 when site is closed!
    if config.IS_CLOSED and config.DEFAULT_ACCESS_ID == 2:
        config.DEFAULT_ACCESS_ID = 1

    return config.DEFAULT_ACCESS_ID

@site.field("language")
def resolve_language(obj, info):
    # pylint: disable=unused-argument
    return config.LANGUAGE

@site.field("logo")
def resolve_logo(obj, info):
    # pylint: disable=unused-argument
    return config.LOGO

@site.field("logoAlt")
def resolve_logo_alt(obj, info):
    # pylint: disable=unused-argument
    return config.LOGO_ALT

@site.field("icon")
def resolve_icon(obj, info):
    # pylint: disable=unused-argument
    return config.ICON if config.ICON else static('icon.svg')

@site.field("iconAlt")
def resolve_icon_alt(obj, info):
    # pylint: disable=unused-argument
    return config.ICON_ALT

@site.field("showIcon")
def resolve_show_icon(obj, info):
    # pylint: disable=unused-argument
    return config.ICON_ENABLED

@site.field("startpage")
def resolve_start_page(obj, info):
    # pylint: disable=unused-argument
    return config.STARTPAGE

@site.field("showLeader")
def resolve_show_leader(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_ENABLED

@site.field("showLeaderButtons")
def resolve_show_leader_buttons(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_BUTTONS_ENABLED

@site.field("subtitle")
def resolve_subtitle(obj, info):
    # pylint: disable=unused-argument
    return config.SUBTITLE

@site.field("leaderImage")
def resolve_leader_image(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_IMAGE

@site.field("showInitiative")
def resolve_show_initiative(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_ENABLED

@site.field("initiativeTitle")
def resolve_initiative_title(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_TITLE

@site.field("initiativeImage")
def resolve_initiative_image(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_IMAGE

@site.field("initiativeImageAlt")
def resolve_initiative_image_alt(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_IMAGE_ALT

@site.field("initiativeDescription")
def resolve_initiative_description(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_DESCRIPTION

@site.field("initiatorLink")
def resolve_initiator_link(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_LINK

@site.field("style")
def resolve_style(obj, info):
    # pylint: disable=unused-argument
    return {
        'font': config.FONT,
        'colorPrimary': config.COLOR_PRIMARY,
        'colorSecondary': config.COLOR_SECONDARY,
        'colorHeader': config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY,
    }

@site.field("customTagsAllowed")
def resolve_custom_tags_allowed(obj, info):
    # pylint: disable=unused-argument
    return config.CUSTOM_TAGS_ENABLED

@site.field("tagCategories")
def resolve_tag_categories(obj, info):
    # pylint: disable=unused-argument
    return config.TAG_CATEGORIES

@site.field("showTagsInFeed")
def resolve_show_tags_in_feed(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_TAGS_IN_FEED

@site.field("showTagsInDetail")
def resolve_show_tags_in_detail(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_TAGS_IN_DETAIL

@site.field("activityFilter")
def resolve_activity_filter(obj, info):
    # pylint: disable=unused-argument
    return get_activity_filters()

@site.field("showExtraHomepageFilters")
def resolve_show_extra_homepage_filters(obj, info):
    # pylint: disable=unused-argument
    return config.ACTIVITY_FEED_FILTERS_ENABLED

@site.field("usersOnline")
def resolve_users_online(obj, info):
    # pylint: disable=unused-argument
    ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
    return UserProfile.objects.filter(last_online__gte=ten_minutes_ago).count()

@site.field("achievementsEnabled")
def resolve_achievements_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.ACHIEVEMENTS_ENABLED

@site.field("cancelMembershipEnabled")
def resolve_cancel_membership(obj, info):
    # pylint: disable=unused-argument
    return config.CANCEL_MEMBERSHIP_ENABLED

@site.field("profileFields")
def resolve_profile_fields(obj, info):
    # pylint: disable=unused-argument
    return ProfileField.objects.all()

@site.field("editUserNameEnabled")
def resolve_edit_user_name_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.EDIT_USER_NAME_ENABLED

@site.field("commentWithoutAccountEnabled")
def resolve_comment_without_account_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.COMMENT_WITHOUT_ACCOUNT_ENABLED
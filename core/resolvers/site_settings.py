from ariadne import ObjectType
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from graphql import GraphQLError

from cms.models import Page
from core import config
from core.constances import USER_ROLES
from core.lib import get_language_options, get_exportable_user_fields, get_exportable_content_types, get_access_ids, get_activity_filters
from core.models import ProfileField, ProfileFieldValidator, SiteInvitation, SiteAccessRequest, UserProfile, ProfileSet
from core.resolvers import shared
from user.models import User

site_settings_private = ObjectType("SiteSettings")
site_settings_public = ObjectType("Site")


@site_settings_public.field('guid')
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return 1


@site_settings_public.field('name')
@site_settings_private.field('name')
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return config.NAME


@site_settings_private.field('description')
def resolve_description(obj, info):
    # pylint: disable=unused-argument
    return config.DESCRIPTION


@site_settings_public.field('language')
@site_settings_private.field('language')
def resolve_language(obj, info):
    # pylint: disable=unused-argument
    return config.LANGUAGE


@site_settings_private.field('languageOptions')
def resolve_language_options(obj, info):
    # pylint: disable=unused-argument
    return get_language_options()


@site_settings_private.field('extraLanguages')
def resolve_extra_languages(obj, info):
    # pylint: disable=unused-argument
    return config.EXTRA_LANGUAGES


@site_settings_private.field('isClosed')
def resolve_is_closed(obj, info):
    # pylint: disable=unused-argument
    return config.IS_CLOSED


@site_settings_private.field('allowRegistration')
def resolve_allow_registration(obj, info):
    # pylint: disable=unused-argument
    return config.ALLOW_REGISTRATION


@site_settings_private.field('directRegistrationDomains')
def resolve_direct_registration_domains(obj, info):
    # pylint: disable=unused-argument
    return config.DIRECT_REGISTRATION_DOMAINS


@site_settings_public.field('defaultAccessId')
@site_settings_private.field('defaultAccessId')
def resolve_default_access_id(obj, info):
    # pylint: disable=unused-argument
    if config.IS_CLOSED and config.DEFAULT_ACCESS_ID == 2:
        config.DEFAULT_ACCESS_ID = 1
    return config.DEFAULT_ACCESS_ID


@site_settings_private.field('defaultAccessIdOptions')
def resolve_default_access_id_options(obj, info):
    # pylint: disable=unused-argument
    defaultAccessIdOptions = [
        {"value": 0, "label": ugettext_lazy("Just me")},
        {"value": 1, "label": ugettext_lazy("Logged in users")}
    ]

    if not config.IS_CLOSED:
        defaultAccessIdOptions.append({"value": 2, "label": ugettext_lazy("Public")})
    else:
        # Reset default access ID when site is closed!
        if config.DEFAULT_ACCESS_ID == 2:
            config.DEFAULT_ACCESS_ID = 1

    return defaultAccessIdOptions


@site_settings_private.field('googleAnalyticsId')
def resolve_google_analytics_id(obj, info):
    # pylint: disable=unused-argument
    return config.GOOGLE_ANALYTICS_ID


@site_settings_private.field('googleSiteVerification')
def resolve_google_site_verification(obj, info):
    # pylint: disable=unused-argument
    return config.GOOGLE_SITE_VERIFICATION


@site_settings_private.field('searchEngineIndexingEnabled')
def resolve_searchengine_indexing_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.ENABLE_SEARCH_ENGINE_INDEXING


@site_settings_private.field('piwikUrl')
def resolve_piwik_url(obj, info):
    # pylint: disable=unused-argument
    return config.PIWIK_URL


@site_settings_private.field('piwikId')
def resolve_piwik_id(obj, info):
    # pylint: disable=unused-argument
    return config.PIWIK_ID


@site_settings_private.field('font')
def resolve_font(obj, info):
    # pylint: disable=unused-argument
    return config.FONT


@site_settings_private.field('colorPrimary')
def resolve_color_primary(obj, info):
    # pylint: disable=unused-argument
    return config.COLOR_PRIMARY


@site_settings_private.field('colorSecondary')
def resolve_color_secondary(obj, info):
    # pylint: disable=unused-argument
    return config.COLOR_SECONDARY


@site_settings_private.field('colorHeader')
def resolve_color_header(obj, info):
    # pylint: disable=unused-argument
    return config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY


@site_settings_public.field('theme')
@site_settings_private.field('theme')
def resolve_theme(obj, info):
    # pylint: disable=unused-argument
    return config.THEME


@site_settings_private.field('themeOptions')
def resolve_theme_options(obj, info):
    # pylint: disable=unused-argument
    return config.THEME_OPTIONS


@site_settings_private.field('fontOptions')
def resolve_font_options(obj, info):
    # pylint: disable=unused-argument
    return [{"value": "Arial", "label": "Arial"},
            {"value": "Open Sans", "label": "Open Sans"},
            {"value": "PT Sans", "label": "PT Sans"},
            {"value": "Rijksoverheid Sans", "label": "Rijksoverheid Sans"},
            {"value": "Roboto", "label": "Roboto"},
            {"value": "Source Sans Pro", "label": "Source Sans Pro"}]


@site_settings_public.field('logo')
@site_settings_private.field('logo')
def resolve_logo(obj, info):
    # pylint: disable=unused-argument
    return config.LOGO


@site_settings_public.field('logoAlt')
@site_settings_private.field('logoAlt')
def resolve_logo_alt(obj, info):
    # pylint: disable=unused-argument
    return config.LOGO_ALT


@site_settings_private.field('favicon')
def resolve_favicon(obj, info):
    # pylint: disable=unused-argument
    return config.FAVICON


@site_settings_private.field('likeIcon')
def resolve_like_icon(obj, info):
    # pylint: disable=unused-argument
    return config.LIKE_ICON


@site_settings_private.field('startPageOptions')
def resolve_start_page_options(obj, info):
    # pylint: disable=unused-argument
    return [{"value": "activity", "label": ugettext_lazy("Activity stream")},
            {"value": "cms", "label": ugettext_lazy("CMS page")}]


@site_settings_public.field('startpage')
@site_settings_private.field('startPage')
def resolve_start_page(obj, info):
    # pylint: disable=unused-argument
    return config.STARTPAGE


@site_settings_private.field('startPageCmsOptions')
def resolve_start_page_cms_options(obj, info):
    # pylint: disable=unused-argument
    start_page_cms_options = []
    for page in Page.objects.all().order_by('title'):
        start_page_cms_options.append({"value": page.guid, "label": page.title})

    return start_page_cms_options


@site_settings_private.field('startPageCms')
def resolve_start_page_cms(obj, info):
    # pylint: disable=unused-argument
    return config.STARTPAGE_CMS


@site_settings_private.field('anonymousStartPage')
def resolve_anonymous_start_page(obj, info):
    # pylint: disable=unused-argument
    return config.ANONYMOUS_START_PAGE


@site_settings_private.field('anonymousStartPageCms')
def resolve_anonymous_start_page_cms(obj, info):
    # pylint: disable=unused-argument
    return config.ANONYMOUS_START_PAGE_CMS


@site_settings_public.field('icon')
@site_settings_private.field('icon')
def resolve_icon(obj, info):
    # pylint: disable=unused-argument
    return config.ICON if config.ICON else static('icon.svg')


@site_settings_public.field('iconAlt')
@site_settings_private.field('iconAlt')
def resolve_icon_alt(obj, info):
    # pylint: disable=unused-argument
    return config.ICON_ALT


@site_settings_public.field('showIcon')
@site_settings_private.field('showIcon')
def resolve_show_icon(obj, info):
    # pylint: disable=unused-argument
    return config.ICON_ENABLED


@site_settings_public.field('menu')
@site_settings_private.field('menu')
def resolve_menu(obj, info):
    # pylint: disable=unused-argument
    return config.MENU


@site_settings_public.field('menuState')
@site_settings_private.field('menuState')
def resolve_menu_state(obj, info):
    # pylint: disable=unused-argument
    return config.MENU_STATE


@site_settings_private.field("numberOfFeaturedItems")
def resolve_number_of_featured_items(obj, info):
    # pylint: disable=unused-argument
    return config.NUMBER_OF_FEATURED_ITEMS


@site_settings_private.field("enableFeedSorting")
def resolve_enable_feed_sorting(obj, info):
    # pylint: disable=unused-argument
    return config.ENABLE_FEED_SORTING


@site_settings_public.field('showExtraHomepageFilters')
@site_settings_private.field('showExtraHomepageFilters')
def resolve_show_extra_homepage_filters(obj, info):
    # pylint: disable=unused-argument
    return config.ACTIVITY_FEED_FILTERS_ENABLED


@site_settings_public.field('showLeader')
@site_settings_private.field('showLeader')
def resolve_show_leader(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_ENABLED


@site_settings_public.field('showLeaderButtons')
@site_settings_private.field('showLeaderButtons')
def resolve_show_leader_buttons(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_BUTTONS_ENABLED


@site_settings_public.field('subtitle')
@site_settings_private.field('subtitle')
def resolve_subtitle(obj, info):
    # pylint: disable=unused-argument
    return config.SUBTITLE


@site_settings_public.field('leaderImage')
@site_settings_private.field('leaderImage')
def resolve_leader_image(obj, info):
    # pylint: disable=unused-argument
    return config.LEADER_IMAGE


@site_settings_public.field('showInitiative')
@site_settings_private.field('showInitiative')
def resolve_show_initiative(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_ENABLED


@site_settings_public.field('initiativeTitle')
@site_settings_private.field('initiativeTitle')
def resolve_initiative_title(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_TITLE


@site_settings_public.field('initiativeDescription')
@site_settings_private.field('initiativeDescription')
def resolve_initiative_description(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_DESCRIPTION


@site_settings_public.field('initiativeImage')
@site_settings_private.field('initiativeImage')
def resolve_initiative_image(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_IMAGE


@site_settings_public.field('initiativeImageAlt')
@site_settings_private.field('initiativeImageAlt')
def resolve_initiative_image_alt(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_IMAGE_ALT


@site_settings_private.field('initiativeLink')
def resolve_initiative_link(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_LINK


@site_settings_public.field('directLinks')
@site_settings_private.field('directLinks')
def resolve_direct_links(obj, info):
    # pylint: disable=unused-argument
    return config.DIRECT_LINKS


@site_settings_public.field('footer')
@site_settings_private.field('footer')
def resolve_footer(obj, info):
    # pylint: disable=unused-argument
    return config.FOOTER


@site_settings_private.field('redirects')
def resolve_redirects(obj, info):
    # pylint: disable=unused-argument
    return [{'source': k, 'destination': v} for k, v in config.REDIRECTS.items()]


@site_settings_public.field('profile')
@site_settings_private.field('profile')
def resolve_profile(obj, info):
    # pylint: disable=unused-argument
    profile_fields = []
    for field in config.PROFILE:
        try:
            profile_fields.append(ProfileField.objects.get(key=field['key']))
        except Exception:
            continue
    return profile_fields


@site_settings_public.field('profileSections')
@site_settings_private.field('profileSections')
def resolve_profile_sections(obj, info):
    # pylint: disable=unused-argument
    return config.PROFILE_SECTIONS


@site_settings_public.field('profileFields')
def resolve_profilefields_public(obj, info):
    # pylint: disable=unused-argument
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    return ProfileField.objects.filter(id__in=profile_section_guids)


@site_settings_private.field('profileFields')
def resolve_profilefields(obj, info):
    # pylint: disable=unused-argument
    return ProfileField.objects.all()


@site_settings_private.field('profileFieldValidators')
def resolve_profile_field_validators(obj, info):
    # pylint: disable=unused-argument
    return ProfileFieldValidator.objects.all()


@site_settings_public.field('tagCategories')
@site_settings_private.field('tagCategories')
def resolve_tag_categories(obj, info):
    # pylint: disable=unused-argument
    return config.TAG_CATEGORIES


@site_settings_public.field('showTagsInFeed')
@site_settings_private.field('showTagsInFeed')
def resolve_show_tags_in_feed(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_TAGS_IN_FEED


@site_settings_public.field('showTagsInDetail')
@site_settings_private.field('showTagsInDetail')
def resolve_show_tags_in_detail(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_TAGS_IN_DETAIL


@site_settings_private.field('defaultEmailOverviewFrequencyOptions')
def resolve_default_email_overview_frequency_options(obj, info):
    # pylint: disable=unused-argument
    return [{"value": "daily", "label": ugettext_lazy("Daily")}, {"value": "weekly", "label": ugettext_lazy("Weekly")},
            {"value": "monthly", "label": ugettext_lazy("Monthly")}, {"value": "never", "label": ugettext_lazy("Never")}]


@site_settings_private.field('defaultEmailOverviewFrequency')
def resolve_default_email_overview_frequency(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY


@site_settings_private.field('emailOverviewSubject')
def resolve_email_overview_subject(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_SUBJECT


@site_settings_private.field('emailOverviewTitle')
def resolve_email_overview_title(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_TITLE


@site_settings_private.field('emailOverviewIntro')
def resolve_email_overview_intro(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_INTRO


@site_settings_private.field('emailOverviewEnableFeatured')
def resolve_email_overview_enable_featured(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_ENABLE_FEATURED


@site_settings_private.field('emailOverviewFeaturedTitle')
def resolve_email_overview_featured_title(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_OVERVIEW_FEATURED_TITLE


@site_settings_private.field('emailNotificationShowExcerpt')
def resolve_email_notification_show_excerpt(obj, info):
    # pylint: disable=unused-argument
    return config.EMAIL_NOTIFICATION_SHOW_EXCERPT


@site_settings_private.field('exportableUserFields')
def resolve_exportable_user_fields(obj, info):
    # pylint: disable=unused-argument
    return get_exportable_user_fields()


@site_settings_private.field('exportableContentTypes')
def resolve_exportable_content_types(obj, info):
    # pylint: disable=unused-argument
    return get_exportable_content_types()


@site_settings_private.field('showLoginRegister')
def resolve_show_login_register(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_LOGIN_REGISTER


@site_settings_public.field('customTagsAllowed')
@site_settings_private.field('customTagsAllowed')
def resolve_custom_tags_allowed(obj, info):
    # pylint: disable=unused-argument
    return config.CUSTOM_TAGS_ENABLED


@site_settings_private.field('showUpDownVoting')
def resolve_show_up_down_voting(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_UP_DOWN_VOTING


@site_settings_private.field('enableSharing')
def resolve_enable_sharing(obj, info):
    # pylint: disable=unused-argument
    return config.ENABLE_SHARING


@site_settings_private.field('showViewsCount')
def resolve_show_views_count(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_VIEW_COUNT


@site_settings_private.field('newsletter')
def resolve_newsletter(obj, info):
    # pylint: disable=unused-argument
    return config.NEWSLETTER


@site_settings_public.field('cancelMembershipEnabled')
@site_settings_private.field('cancelMembershipEnabled')
def resolve_cancel_membership_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.CANCEL_MEMBERSHIP_ENABLED


@site_settings_private.field('showExcerptInNewsCard')
def resolve_show_excerpt_in_news_card(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_EXCERPT_IN_NEWS_CARD


@site_settings_private.field('commentsOnNews')
def resolve_comments_on_news(obj, info):
    # pylint: disable=unused-argument
    return config.COMMENT_ON_NEWS


@site_settings_private.field('eventExport')
def resolve_event_export(obj, info):
    # pylint: disable=unused-argument
    return config.EVENT_EXPORT


@site_settings_private.field('eventTiles')
def resolve_event_tiles(obj, info):
    # pylint: disable=unused-argument
    return config.EVENT_TILES


@site_settings_private.field('questionerCanChooseBestAnswer')
def resolve_questioner_can_choose_best_answer(obj, info):
    # pylint: disable=unused-argument
    return config.QUESTIONER_CAN_CHOOSE_BEST_ANSWER


@site_settings_private.field('statusUpdateGroups')
def resolve_status_update_groups(obj, info):
    # pylint: disable=unused-argument
    return config.STATUS_UPDATE_GROUPS


@site_settings_private.field('subgroups')
def resolve_subgroups(obj, info):
    # pylint: disable=unused-argument
    return config.SUBGROUPS


@site_settings_private.field('groupMemberExport')
def resolve_group_member_export(obj, info):
    # pylint: disable=unused-argument
    return config.GROUP_MEMBER_EXPORT


@site_settings_private.field('limitedGroupAdd')
def resolve_limited_group_add(obj, info):
    # pylint: disable=unused-argument
    return config.LIMITED_GROUP_ADD


@site_settings_public.field('showSuggestedItems')
@site_settings_private.field('showSuggestedItems')
def resolve_show_suggested_items(obj, info):
    # pylint: disable=unused-argument
    return config.SHOW_SUGGESTED_ITEMS


@site_settings_public.field('accessIds')
def resolve_access_ids(obj, info):
    # pylint: disable=unused-argument
    return get_access_ids()


@site_settings_public.field('initiatorLink')
def resolve_initiator_link(obj, info):
    # pylint: disable=unused-argument
    return config.INITIATIVE_LINK


@site_settings_public.field("style")
def resolve_style(obj, info):
    # pylint: disable=unused-argument
    return {
        'font': config.FONT,
        'colorPrimary': config.COLOR_PRIMARY,
        'colorSecondary': config.COLOR_SECONDARY,
        'colorHeader': config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY,
    }


@site_settings_public.field('activityFilter')
def resolve_activity_filter(obj, info):
    # pylint: disable=unused-argument
    return get_activity_filters()


@site_settings_public.field('usersOnline')
def resolve_users_online(obj, info):
    # pylint: disable=unused-argument
    ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
    return UserProfile.objects.filter(last_online__gte=ten_minutes_ago).count()


@site_settings_public.field('achievementsEnabled')
def resolve_achievements_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.ACHIEVEMENTS_ENABLED


@site_settings_public.field('onboardingEnabled')
@site_settings_private.field('onboardingEnabled')
def resolve_onboarding_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.ONBOARDING_ENABLED


@site_settings_private.field('onboardingForceExistingUsers')
def resolve_onboarding_force_existing_users(obj, info):
    # pylint: disable=unused-argument
    return config.ONBOARDING_FORCE_EXISTING_USERS


@site_settings_public.field('onboardingIntro')
@site_settings_private.field('onboardingIntro')
def resolve_onboarding_intro(obj, info):
    # pylint: disable=unused-argument
    return config.ONBOARDING_INTRO


@site_settings_private.field('siteInvites')
def resolve_site_invites(obj, info):
    # pylint: disable=unused-argument
    return {'edges': SiteInvitation.objects.all()}


@site_settings_private.field('cookieConsent')
def resolve_cookie_consent(obj, info):
    # pylint: disable=unused-argument
    return config.COOKIE_CONSENT


@site_settings_private.field('loginIntro')
def resolve_login_intro(obj, info):
    # pylint: disable=unused-argument
    return config.LOGIN_INTRO


@site_settings_private.field('roleOptions')
def resolve_role_options(obj, info):
    # pylint: disable=unused-argument
    return [{'value': USER_ROLES.ADMIN, 'label': ugettext_lazy('Administrator')},
            {'value': USER_ROLES.EDITOR, 'label': ugettext_lazy('Editor')},
            {'value': USER_ROLES.QUESTION_MANAGER, 'label': ugettext_lazy('Question expert')}]


@site_settings_private.field('siteAccessRequests')
def resolve_site_access_requests(obj, info):
    # pylint: disable=unused-argument
    return {'edges': SiteAccessRequest.objects.filter(accepted=False)}


@site_settings_private.field('deleteAccountRequests')
def resolve_delete_account_requests(obj, info):
    # pylint: disable=unused-argument
    return {'edges': User.objects.filter(is_delete_requested=True).all()}


@site_settings_private.field('profileSyncEnabled')
def resolve_profile_sync_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.PROFILE_SYNC_ENABLED


@site_settings_private.field('profileSyncToken')
def resolve_profile_sync_token(obj, info):
    # pylint: disable=unused-argument
    return config.PROFILE_SYNC_TOKEN


@site_settings_private.field('customCss')
def resolve_custom_css(obj, info):
    # pylint: disable=unused-argument
    return config.CUSTOM_CSS


@site_settings_private.field('walledGardenByIpEnabled')
def resolve_walled_garden_by_ip_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.WALLED_GARDEN_BY_IP_ENABLED


@site_settings_private.field('whitelistedIpRanges')
def resolve_whitelisted_ip_ranges(obj, info):
    # pylint: disable=unused-argument
    return config.WHITELISTED_IP_RANGES


@site_settings_private.field('siteMembershipAcceptedIntro')
def resolve_site_membership_accepted_intro(obj, info):
    # pylint: disable=unused-argument
    return config.SITE_MEMBERSHIP_ACCEPTED_INTRO


@site_settings_private.field('siteMembershipDeniedIntro')
def resolve_site_membership_denied_intro(obj, info):
    # pylint: disable=unused-argument
    return config.SITE_MEMBERSHIP_DENIED_INTRO


@site_settings_private.field('idpId')
def resolve_idp_id(obj, info):
    # pylint: disable=unused-argument
    return config.IDP_ID


@site_settings_private.field('idpName')
def resolve_idp_name(obj, info):
    # pylint: disable=unused-argument
    return config.IDP_NAME


@site_settings_private.field('autoApproveSSO')
def resolve_auto_approve_sso(obj, info):
    # pylint: disable=unused-argument
    return config.AUTO_APPROVE_SSO


@site_settings_private.field('require2FA')
def resolve_require_2fa(obj, info):
    # pylint: disable=unused-argument
    return config.REQUIRE_2FA


# TODO: remove after flow connects to general api
@site_settings_private.field('flowEnabled')
def resolve_flow_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_ENABLED


@site_settings_private.field('flowSubtypes')
def resolve_flow_subtypes(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_SUBTYPES


@site_settings_private.field('flowAppUrl')
def resolve_flow_app_url(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_APP_URL


@site_settings_private.field('flowToken')
def resolve_flow_token(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_TOKEN


@site_settings_private.field('flowCaseId')
def resolve_flow_case_id(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_CASE_ID


@site_settings_private.field('flowUserGuid')
def resolve_flow_user_guid(obj, info):
    # pylint: disable=unused-argument
    return config.FLOW_USER_GUID


@site_settings_public.field('editUserNameEnabled')
@site_settings_private.field('editUserNameEnabled')
def resolve_edit_user_name_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.EDIT_USER_NAME_ENABLED


@site_settings_public.field('commentWithoutAccountEnabled')
@site_settings_private.field('commentWithoutAccountEnabled')
def resolve_comment_without_account_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.COMMENT_WITHOUT_ACCOUNT_ENABLED


@site_settings_public.field('questionLockAfterActivity')
@site_settings_private.field('questionLockAfterActivity')
def resolve_question_lock_after_activity(obj, info):
    # pylint: disable=unused-argument
    return config.QUESTION_LOCK_AFTER_ACTIVITY


@site_settings_public.field('questionLockAfterActivityLink')
@site_settings_private.field('questionLockAfterActivityLink')
def resolve_question_lock_after_activity_link(obj, info):
    # pylint: disable=unused-argument
    return config.QUESTION_LOCK_AFTER_ACTIVITY_LINK


@site_settings_private.field('kalturaVideoEnabled')
def resolve_kaltura_video_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.KALTURA_VIDEO_ENABLED


@site_settings_private.field('kalturaVideoPartnerId')
def resolve_kaltura_video_partner_id(obj, info):
    # pylint: disable=unused-argument
    return config.KALTURA_VIDEO_PARTNER_ID


@site_settings_private.field('kalturaVideoPlayerId')
def resolve_kaltura_video_player_id(obj, info):
    # pylint: disable=unused-argument
    return config.KALTURA_VIDEO_PLAYER_ID


@site_settings_public.field('fileDescriptionFieldEnabled')
@site_settings_private.field('fileDescriptionFieldEnabled')
def resolve_file_description_field_enabled(obj, info):
    # pylint: disable=unused-argument
    return 'enable_file_description' in config.FILE_OPTIONS


@site_settings_public.field('pdfCheckerEnabled')
@site_settings_private.field('pdfCheckerEnabled')
def resolve_pdf_checker_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.PDF_CHECKER_ENABLED


@site_settings_public.field('maxCharactersInAbstract')
@site_settings_private.field('maxCharactersInAbstract')
def resolve_max_characters_in_abstract(obj, info):
    # pylint: disable=unused-argument
    return config.MAX_CHARACTERS_IN_ABSTRACT


@site_settings_public.field('collabEditingEnabled')
@site_settings_private.field('collabEditingEnabled')
def resolve_collab_editing_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.COLLAB_EDITING_ENABLED


@site_settings_public.field('preserveFileExif')
@site_settings_private.field('preserveFileExif')
def resolve_preserve_file_exif(obj, info):
    # pylint: disable=unused-argument
    return config.PRESERVE_FILE_EXIF


@site_settings_public.field("scheduleAppointmentEnabled")
def resolve_schedule_appointment_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.ONLINEAFSPRAKEN_ENABLED


@site_settings_public.field("videocallEnabled")
def resolve_schedule_videocall_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.VIDEOCALL_ENABLED


@site_settings_public.field("videocallProfilepage")
def resolve_videocall_profilepage(*args):
    # pylint: disable=unused-argument
    return config.VIDEOCALL_PROFILEPAGE


@site_settings_private.field('supportContractEnabled')
def resolve_support_contract_enabled(obj, info):
    # pylint: disable=unused-argument
    return config.SUPPORT_CONTRACT_ENABLED


@site_settings_private.field('supportContractHoursRemaining')
def resolve_support_contract_hours_remaining(obj, info):
    # pylint: disable=unused-argument
    return config.SUPPORT_CONTRACT_HOURS_REMAINING


@site_settings_private.field("appointmentTypeVideocall")
def resolve_appointment_type_videocall(obj, info):
    # pylint: disable=unused-argument
    try:
        shared.assert_meetings_enabled()
        return shared.resolve_load_appointment_types()
    except GraphQLError:
        pass


@site_settings_private.field("profileSets")
def resolve_profile_sets(obj, info):
    # pylint: disable=unused-argument
    return ProfileSet.objects.all()


@site_settings_public.field("searchArchiveOption")
@site_settings_private.field("searchArchiveOption")
def resolve_searchArchiveOption(obj, info):
    # pylint: disable=unused-argument
    return config.SEARCH_ARCHIVE_OPTION


@site_settings_public.field('blockedUserIntroMessage')
@site_settings_private.field('blockedUserIntroMessage')
def resolve_blocked_user_intro_message(obj, info):
    # pylint: disable=unused-argument
    return config.BLOCKED_USER_INTRO_MESSAGE

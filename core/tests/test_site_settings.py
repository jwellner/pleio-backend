from unittest import mock
import uuid

from django.db import connection
from django.utils import timezone

from core.models import ProfileField, SiteInvitation, SiteAccessRequest, Setting
from core.tests.helpers import PleioTenantTestCase, override_config
from user.factories import UserFactory, AdminFactory
from user.models import User
from cms.models import Page
from django.core.cache import cache
from mixer.backend.django import mixer
from core.lib import get_language_options, datetime_utciso


def time_factory(**kwargs):
    return timezone.localtime() + timezone.timedelta(**kwargs)


class TestSiteSettingsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User, is_delete_requested=False)
        self.admin = mixer.blend(User, roles=['ADMIN'], is_delete_requested=False)
        self.delete_user = mixer.blend(User, is_delete_requested=True)
        self.cmsPage1 = mixer.blend(Page, title="Z title")
        self.cmsPage2 = mixer.blend(Page, title="A title")
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')
        self.siteInvitation = mixer.blend(SiteInvitation, email='a@a.nl')
        self.siteAccessRequest0 = mixer.blend(SiteAccessRequest, email='johnny.a@example.com', name='Johnny A.',
                                              created_at=time_factory(days=-10))
        self.siteAccessRequest1 = mixer.blend(SiteAccessRequest, email='johnny.b@example.com', name='Johnny B.',
                                              created_at=time_factory(days=-5))
        self.siteAccessRequest2 = mixer.blend(SiteAccessRequest, email='johnny.c@example.com', name='Johnny C.',
                                              created_at=time_factory(days=-7))
        self.siteApprovedRequest0 = mixer.blend(SiteAccessRequest, email='johnny.d@example.com', name='Johnny D.', accepted=True,
                                                updated_at=time_factory(days=-6))
        self.siteApprovedRequest1 = mixer.blend(SiteAccessRequest, email='johnny.e@example.com', name='Johnny E.', accepted=True,
                                                updated_at=time_factory(days=-2))
        self.siteApprovedRequest2 = mixer.blend(SiteAccessRequest, email='johnny.f@example.com', name='Johnny F.', accepted=True,
                                                updated_at=time_factory(days=-4))

        self.query = """
            query SiteGeneralSettings {
                siteSettings {
                    languageOptions {
                        value
                        label
                    }
                    language
                    extraLanguages
                    name
                    isClosed
                    allowRegistration
                    directRegistrationDomains
                    defaultAccessIdOptions {
                        value
                        label
                    }
                    defaultAccessId
                    googleAnalyticsId
                    googleSiteVerification
                    searchEngineIndexingEnabled
                    piwikUrl
                    piwikId

                    themeOptions {
                        value
                        label
                    }
                    fontOptions {
                        value
                        label
                    }
                    font
                    colorHeader
                    colorPrimary
                    colorSecondary
                    theme
                    logo
                    logoAlt
                    favicon
                    likeIcon

                    startPageOptions {
                        value
                        label
                    }
                    startPage
                    startPageCmsOptions {
                        value
                        label
                    }
                    startPageCms
                    anonymousStartPage
                    anonymousStartPageCms
                    showIcon
                    icon
                    menu {
                        title
                        link
                        children {
                            title
                            link
                            accessId
                        }
                        accessId
                    }

                    numberOfFeaturedItems
                    enableFeedSorting
                    showExtraHomepageFilters
                    showLeader
                    showLeaderButtons
                    subtitle
                    leaderImage
                    showInitiative
                    initiativeTitle
                    initiativeDescription
                    initiativeImage
                    initiativeImageAlt
                    initiativeLink
                    directLinks {
                        title
                        link
                    }
                    footer {
                        title
                        link
                    }
                    redirects {
                        source
                        destination
                    }
                    profile {
                        key
                        name
                        isFilterable
                        isFilter
                    }

                    profileFields {
                        key
                    }

                    tagCategories {
                        name
                        values
                    }
                    showTagsInFeed
                    showTagsInDetail

                    defaultEmailOverviewFrequencyOptions {
                        value
                        label
                    }
                    defaultEmailOverviewFrequency
                    emailOverviewSubject
                    emailOverviewTitle
                    emailOverviewIntro
                    emailNotificationShowExcerpt

                    exportableUserFields {
                        field_type
                        field
                        label
                    }

                    exportableContentTypes {
                        value
                        label
                    }

                    showLoginRegister
                    customTagsAllowed
                    showUpDownVoting
                    enableSharing
                    showViewsCount
                    newsletter
                    cancelMembershipEnabled
                    showExcerptInNewsCard
                    commentsOnNews
                    eventExport
                    eventTiles
                    questionerCanChooseBestAnswer
                    statusUpdateGroups
                    subgroups
                    groupMemberExport
                    showSuggestedItems

                    onboardingEnabled
                    onboardingForceExistingUsers
                    onboardingIntro
                    siteInvites {
                        edges {
                            email
                        }
                    }
                    cookieConsent
                    roleOptions {
                        value
                        label
                    }
                    siteAccessRequests {
                        edges {
                            email
                            name
                            status
                            timeCreated
                            timeUpdated
                        }
                    }
                    siteAccessApproved {
                        edges {
                            email
                        }
                    }
                    deleteAccountRequests {
                        edges {
                            guid
                        }
                    }

                    profileSyncEnabled
                    profileSyncToken

                    customCss
                    walledGardenByIpEnabled
                    whitelistedIpRanges
                    siteMembershipAcceptedIntro
                    siteMembershipDeniedIntro
                    idpId
                    idpName
                    autoApproveSSO

                    flowEnabled
                    flowSubtypes
                    flowAppUrl
                    flowToken
                    flowCaseId
                    flowUserGuid

                    commentWithoutAccountEnabled

                    kalturaVideoEnabled
                    kalturaVideoPartnerId
                    kalturaVideoPlayerId

                    pdfCheckerEnabled
                    collabEditingEnabled
                    sitePlan
                    supportContractEnabled
                    supportContractHoursRemaining
                    searchArchiveOption
                    blockedUserIntroMessage
                    
                    appointmentTypeVideocall {
                        name
                        hasVideocall
                    }

                    pushNotificationsEnabled
                    
                    pageTagFilters {
                        showTagFilter
                        showTagCategories
                        contentType
                    }
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_site_settings_by_admin(self):

        with override_config(
            IS_CLOSED=False,
            ANONYMOUS_START_PAGE='cms',
            ANONYMOUS_START_PAGE_CMS=self.cmsPage2.guid,
            PAGE_TAG_FILTERS=[{
                'showTagFilter': False,
                'showTagCategories': [],
                'contentType': 'blog'
            }]
        ):
            self.graphql_client.force_login(self.admin)
            result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["siteSettings"]["name"], "Pleio 2.0")
        self.assertEqual(data["siteSettings"]["language"], "nl")
        self.assertEqual(data["siteSettings"]["extraLanguages"], [])
        self.assertEqual(data["siteSettings"]["languageOptions"], get_language_options())
        self.assertEqual(data["siteSettings"]["isClosed"], False)
        self.assertEqual(data["siteSettings"]["allowRegistration"], True)
        self.assertEqual(data["siteSettings"]["directRegistrationDomains"], [])
        self.assertEqual(data["siteSettings"]["defaultAccessIdOptions"],
                         [{'value': 0, 'label': 'Alleen eigenaar'}, {'value': 1, 'label': 'Ingelogde gebruikers'},
                          {'value': 2, 'label': 'Iedereen (publiek zichtbaar)'}])
        self.assertEqual(data["siteSettings"]["defaultAccessId"], 1)
        self.assertEqual(data["siteSettings"]["googleAnalyticsId"], "")
        self.assertEqual(data["siteSettings"]["googleSiteVerification"], "")
        self.assertEqual(data["siteSettings"]["searchEngineIndexingEnabled"], False)
        self.assertEqual(data["siteSettings"]["piwikUrl"], "https://stats.pleio.nl/")
        self.assertEqual(data["siteSettings"]["piwikId"], "")

        self.assertEqual(data["siteSettings"]["themeOptions"], [{"value": 'leraar', 'label': 'Standaard'},
                                                                {'value': 'rijkshuisstijl', 'label': 'Rijkshuisstijl'}])
        self.assertEqual(data["siteSettings"]["fontOptions"], [
            {"value": "Arial", "label": "Arial"},
            {"value": "Open Sans", "label": "Open Sans"},
            {"value": "Palanquin", "label": "Palanquin"},
            {"value": "PT Sans", "label": "PT Sans"},
            {"value": "Rijksoverheid Sans", "label": "Rijksoverheid Sans"},
            {"value": "Roboto", "label": "Roboto"},
            {"value": "Source Sans Pro", "label": "Source Sans Pro"},
            {"value": "Source Serif Pro", "label": "Source Serif Pro"}
        ])

        self.assertEqual(data["siteSettings"]["font"], "Rijksoverheid Sans")
        self.assertEqual(data["siteSettings"]["colorHeader"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorPrimary"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorSecondary"], "#009ee3")
        self.assertEqual(data["siteSettings"]["theme"], "leraar")
        self.assertEqual(data["siteSettings"]["logo"], "")
        self.assertEqual(data["siteSettings"]["logoAlt"], "")
        self.assertEqual(data["siteSettings"]["favicon"], "")
        self.assertEqual(data["siteSettings"]["likeIcon"], "heart")

        self.assertEqual(data['siteSettings']['anonymousStartPage'], 'cms')
        self.assertEqual(data['siteSettings']['anonymousStartPageCms'], self.cmsPage2.guid)
        self.assertEqual(data["siteSettings"]["startPageOptions"],
                         [{"value": "activity", "label": "Activiteitenstroom"},
                          {"value": "cms", "label": "CMS pagina"}])
        self.assertEqual(data["siteSettings"]["startPage"], "activity")
        self.assertEqual(data["siteSettings"]["startPageCmsOptions"], [
            {"value": self.cmsPage2.guid, 'label': self.cmsPage2.title},
            {"value": self.cmsPage1.guid, 'label': self.cmsPage1.title}
        ])
        self.assertEqual(data["siteSettings"]["startPageCms"], "")
        self.assertEqual(data["siteSettings"]["showIcon"], False)
        self.assertIn("/static/icon", data["siteSettings"]["icon"])  # show default'':
        self.assertEqual(data["siteSettings"]["menu"], [
            {"link": "/blog", "title": "Blog", "children": [], "accessId": 2},
            {"link": "/news", "title": "Nieuws", "children": [], "accessId": 2},
            {"link": "/groups", "title": "Groepen", "children": [], "accessId": 2},
            {"link": "/questions", "title": "Vragen", "children": [], "accessId": 2},
            {"link": "/wiki", "title": "Wiki", "children": [], "accessId": 2}
        ])

        self.assertEqual(data["siteSettings"]["numberOfFeaturedItems"], 0)
        self.assertEqual(data["siteSettings"]["enableFeedSorting"], False)
        self.assertEqual(data["siteSettings"]["showExtraHomepageFilters"], True)
        self.assertEqual(data["siteSettings"]["showLeader"], False)
        self.assertEqual(data["siteSettings"]["showLeaderButtons"], False)
        self.assertEqual(data["siteSettings"]["subtitle"], "")
        self.assertEqual(data["siteSettings"]["leaderImage"], "")
        self.assertEqual(data["siteSettings"]["showInitiative"], False)
        self.assertEqual(data["siteSettings"]["initiativeTitle"], "")
        self.assertEqual(data["siteSettings"]["initiativeDescription"], "")
        self.assertEqual(data["siteSettings"]["initiativeImage"], "")
        self.assertEqual(data["siteSettings"]["initiativeImageAlt"], "")
        self.assertEqual(data["siteSettings"]["initiativeLink"], "")
        self.assertEqual(data["siteSettings"]["directLinks"], [])
        self.assertEqual(data["siteSettings"]["footer"], [])
        self.assertEqual(data["siteSettings"]["redirects"], [])

        self.assertEqual(data["siteSettings"]["profile"], [])
        self.assertEqual(data["siteSettings"]["profileFields"],
                         [{"key": self.profileField1.key}, {"key": self.profileField2.key}])

        self.assertEqual(data["siteSettings"]["tagCategories"], [])
        self.assertEqual(data["siteSettings"]["showTagsInFeed"], False)
        self.assertEqual(data["siteSettings"]["showTagsInDetail"], False)

        self.assertEqual(data["siteSettings"]["defaultEmailOverviewFrequencyOptions"], [
            {"value": "daily", "label": "Dagelijks"},
            {"value": "weekly", "label": "Wekelijks"},
            {"value": "monthly", "label": "Maandelijks"},
            {"value": "never", "label": "Nooit"}
        ])
        self.assertEqual(data["siteSettings"]["defaultEmailOverviewFrequency"], "weekly")
        self.assertEqual(data["siteSettings"]["emailOverviewSubject"], "")
        self.assertEqual(data["siteSettings"]["emailOverviewTitle"], "Pleio 2.0")
        self.assertEqual(data["siteSettings"]["emailOverviewIntro"], "")
        self.assertEqual(data["siteSettings"]["emailNotificationShowExcerpt"], False)

        self.assertEqual(data["siteSettings"]["onboardingEnabled"], False)
        self.assertEqual(data["siteSettings"]["onboardingForceExistingUsers"], False)
        self.assertEqual(data["siteSettings"]["onboardingIntro"], "")

        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["field_type"], "userField")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["field"], "guid")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["label"], "guid")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["field_type"], "userField")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["field"], "banned")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["label"], "banned")

        self.assertEqual(data["siteSettings"]["exportableContentTypes"], [
            {"value": "statusupdate", "label": "Updates"},
            {"value": "blog", "label": "Blogs"},
            {"value": "page", "label": "CMS pagina's"},
            {"value": "discussion", "label": "Discussies"},
            {"value": "event", "label": "Agenda-items"},
            {"value": "file", "label": "Bestanden"},
            {"value": "news", "label": "Nieuws"},
            {"value": "poll", "label": "Polls"},
            {"value": "question", "label": "Vragen"},
            {"value": "task", "label": "Taken"},
            {"value": "wiki", "label": "Wiki pagina's"},
            {'value': 'comment', 'label': 'Reacties'},
            {'value': 'group', 'label': 'Groepen'}
        ])

        self.assertEqual(data["siteSettings"]["showLoginRegister"], True)
        self.assertEqual(data["siteSettings"]["customTagsAllowed"], True)
        self.assertEqual(data["siteSettings"]["showUpDownVoting"], True)
        self.assertEqual(data["siteSettings"]["enableSharing"], True)
        self.assertEqual(data["siteSettings"]["showViewsCount"], True)
        self.assertEqual(data["siteSettings"]["newsletter"], False)
        self.assertEqual(data["siteSettings"]["cancelMembershipEnabled"], True)
        self.assertEqual(data["siteSettings"]["showExcerptInNewsCard"], False)
        self.assertEqual(data["siteSettings"]["commentsOnNews"], False)
        self.assertEqual(data["siteSettings"]["eventExport"], False)
        self.assertEqual(data["siteSettings"]["eventTiles"], False)
        self.assertEqual(data["siteSettings"]["questionerCanChooseBestAnswer"], False)
        self.assertEqual(data["siteSettings"]["statusUpdateGroups"], True)
        self.assertEqual(data["siteSettings"]["subgroups"], False)
        self.assertEqual(data["siteSettings"]["groupMemberExport"], False)
        self.assertEqual(data["siteSettings"]["showSuggestedItems"], False)
        self.assertEqual(data["siteSettings"]["siteInvites"]["edges"][0]['email'], 'a@a.nl')
        self.assertEqual(data["siteSettings"]["cookieConsent"], False)
        self.assertEqual(data["siteSettings"]["roleOptions"],
                         [{'value': 'ADMIN', 'label': 'Beheerder'}, {'value': 'EDITOR', 'label': 'Redacteur'},
                          {'value': 'QUESTION_MANAGER', 'label': 'Vraagexpert'}])
        pending_requests = [r['email'] for r in data["siteSettings"]["siteAccessRequests"]["edges"]]
        self.assertEqual(pending_requests, ['johnny.a@example.com', 'johnny.c@example.com', 'johnny.b@example.com'])
        accepted_requests = [r['email'] for r in data["siteSettings"]["siteAccessApproved"]["edges"]]
        self.assertEqual(accepted_requests, ['johnny.e@example.com', 'johnny.f@example.com', 'johnny.d@example.com'])
        self.assertEqual(data["siteSettings"]["siteAccessRequests"]["edges"][0], {
            "email": self.siteAccessRequest0.email,
            "name": self.siteAccessRequest0.name,
            "status": "pending",
            "timeCreated": datetime_utciso(self.siteAccessRequest0.created_at),
            "timeUpdated": datetime_utciso(self.siteAccessRequest0.updated_at),
        })
        self.assertEqual(data["siteSettings"]["deleteAccountRequests"]["edges"][0]['guid'], self.delete_user.guid)
        self.assertEqual(data["siteSettings"]["profileSyncEnabled"], False)
        self.assertEqual(data["siteSettings"]["profileSyncToken"], "")
        self.assertEqual(data["siteSettings"]["customCss"], "")
        self.assertEqual(data["siteSettings"]["whitelistedIpRanges"], [])
        self.assertEqual(data["siteSettings"]["walledGardenByIpEnabled"], False)
        self.assertEqual(data["siteSettings"]["siteMembershipAcceptedIntro"], "")
        self.assertEqual(data["siteSettings"]["siteMembershipDeniedIntro"], "")
        self.assertEqual(data["siteSettings"]["idpId"], "")
        self.assertEqual(data["siteSettings"]["idpName"], "")
        self.assertEqual(data["siteSettings"]["autoApproveSSO"], False)
        # TODO: remove after flow connects to general api
        self.assertEqual(data["siteSettings"]["flowEnabled"], False)
        self.assertEqual(data["siteSettings"]["flowSubtypes"], [])
        self.assertEqual(data["siteSettings"]["flowAppUrl"], "")
        self.assertEqual(data["siteSettings"]["flowToken"], "")
        self.assertEqual(data["siteSettings"]["flowCaseId"], None)
        self.assertEqual(data["siteSettings"]["flowUserGuid"], "")
        self.assertEqual(data["siteSettings"]["commentWithoutAccountEnabled"], False)
        self.assertEqual(data["siteSettings"]["kalturaVideoEnabled"], False)
        self.assertEqual(data["siteSettings"]["kalturaVideoPartnerId"], "")
        self.assertEqual(data["siteSettings"]["kalturaVideoPlayerId"], "")
        self.assertEqual(data["siteSettings"]["pdfCheckerEnabled"], True)
        self.assertEqual(data["siteSettings"]["collabEditingEnabled"], False)
        self.assertEqual(data["siteSettings"]['sitePlan'], '')
        self.assertEqual(data["siteSettings"]["supportContractEnabled"], False)
        self.assertEqual(data["siteSettings"]["supportContractHoursRemaining"], 0)
        self.assertEqual(data['siteSettings']["searchArchiveOption"], 'nobody')
        self.assertEqual(data["siteSettings"]["blockedUserIntroMessage"], '')
        self.assertEqual(data["siteSettings"]["pushNotificationsEnabled"], False)
        self.assertEqual(data["siteSettings"]["pageTagFilters"], [{'contentType': 'news', 'showTagFilter': True, 'showTagCategories': []},
                                                                  {'contentType': 'blog', 'showTagFilter': False, 'showTagCategories': []},
                                                                  {'contentType': 'question', 'showTagFilter': True, 'showTagCategories': []},
                                                                  {'contentType': 'discussion', 'showTagFilter': True, 'showTagCategories': []},
                                                                  {'contentType': 'event', 'showTagFilter': False, 'showTagCategories': []}])

    def test_site_settings_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.query, {})

    def test_site_settings_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {})

    def test_site_settings_menu_state_normal(self):
        query = """
        mutation UpdateFileOptions($input: editSiteSettingInput!) {
            editSiteSetting(input: $input) {
                siteSettings {
                    menuState
                    __typename
                }
                __typename
            }
        }
        """
        variables = {
            'input': {
                'menuState': 'normal',
            }
        }
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, variables)

        self.assertEqual(result['data']['editSiteSetting']['siteSettings']['menuState'], 'normal', msg=result)

    def test_site_settings_menu_state_compact(self):
        query = """
        mutation UpdateFileOptions($input: editSiteSettingInput!) {
            editSiteSetting(input: $input) {
                siteSettings {
                    menuState
                    __typename
                }
                __typename
            }
        }
        """
        variables = {
            'input': {
                'menuState': 'compact',
            }
        }
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, variables)

        self.assertEqual(result['data']['editSiteSetting']['siteSettings']['menuState'], 'compact', msg=result)

    def test_site_settings_file_description_enabled(self):
        query = """
        mutation UpdateFileOptions($input: editSiteSettingInput!) {
            editSiteSetting(input: $input) {
                siteSettings {
                    fileDescriptionFieldEnabled
                    __typename
                }
                __typename
            }
        }
        """
        variables = {
            'input': {
                'fileDescriptionFieldEnabled': True,
            }
        }
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, variables)

        self.assertTrue(result['data']['editSiteSetting']['siteSettings']['fileDescriptionFieldEnabled'], msg=result)

    def test_site_settings_file_description_disabled(self):
        query = """
        mutation UpdateFileOptions($input: editSiteSettingInput!) {
            editSiteSetting(input: $input) {
                siteSettings {
                    fileDescriptionFieldEnabled
                    __typename
                }
                __typename
            }
        }
        """
        variables = {
            'input': {
                'fileDescriptionFieldEnabled': False,
            }
        }
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, variables)

        self.assertFalse(result['data']['editSiteSetting']['siteSettings']['fileDescriptionFieldEnabled'], msg=result)

    @mock.patch('core.resolvers.shared.MeetingsApi.get_appointment_types')
    def test_query_no_videocall_settings(self, get_appointment_types):
        get_appointment_types.return_value = [{"Id": "1000", "Name": "First"},
                                              {"Id": "1001", "Name": "Second"}]

        with override_config(VIDEOCALL_APPOINTMENT_TYPE=None,
                             ONLINEAFSPRAKEN_ENABLED=True):
            self.graphql_client.force_login(self.admin)
            response = self.graphql_client.post(self.query, {})

        self.assertEqual(response['data']['siteSettings']['appointmentTypeVideocall'], [
            {"name": "First",
             "hasVideocall": False},
            {"name": "Second",
             "hasVideocall": False},
        ])

    @mock.patch('core.resolvers.shared.MeetingsApi.get_appointment_types')
    def test_query_videocall_settings(self, get_appointment_types):
        get_appointment_types.return_value = [{"Id": "1000", "Name": "First"},
                                              {"Id": "1001", "Name": "Second"}]

        with override_config(VIDEOCALL_APPOINTMENT_TYPE=[{"id": "1000", "hasVideocall": True}],
                             ONLINEAFSPRAKEN_ENABLED=True):
            self.graphql_client.force_login(self.admin)
            response = self.graphql_client.post(self.query, {})

        self.assertEqual(
            response['data']['siteSettings']['appointmentTypeVideocall'],
            [{"name": 'First',
              "hasVideocall": True
              },
             {"name": "Second",
              "hasVideocall": False}]
        )

    @override_config(ONLINEAFSPRAKEN_ENABLED=True)
    @mock.patch('core.resolvers.shared.MeetingsApi.get_appointment_types')
    def test_update_videocall_settings(self, get_appointment_types):
        get_appointment_types.return_value = [{"Id": "1000", "Name": "First"},
                                              {"Id": "1001", "Name": "Second"}]

        mutation = """
        mutation UpdateSiteSettings($input: editSiteSettingInput!) {
            m: editSiteSetting(input: $input) {
                r: siteSettings {
                    appointmentTypeVideocall {
                        name
                        hasVideocall
                    }
                }
            }
        }
        """

        setting, _ = Setting.objects.get_or_create(key='VIDEOCALL_APPOINTMENT_TYPE')
        setting.value = [{"id": "1000", "hasVideocall": True}]
        setting.save()
    
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(mutation, {"input": {
            "appointmentTypeVideocall": [
                {"id": "1000", "hasVideocall": False},
                {"id": "1001", "hasVideocall": True},
            ]
        }})

        self.assertEqual(response['data']['m']['r']['appointmentTypeVideocall'], [
            {"name": "First", "hasVideocall": False},
            {"name": "Second","hasVideocall": True},
        ])

        setting.refresh_from_db()

        self.assertEqual(setting.value, [
            {"id": "1000", "hasVideocall": False},
            {"id": "1001", "hasVideocall": True},
        ])

        setting.delete()


class TestSiteSettingsIsClosedTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_random(self):
        response = self.client.get("/981random3")
        self.assertTemplateUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_graphql(self):
        response = self.client.get("/graphql")
        self.assertTemplateUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_robots(self):
        response = self.client.get("/robots.txt")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_sitemap(self):
        response = self.client.get("/sitemap.xml")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_oidc(self):
        response = self.client.get("/oidc/test")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_login(self):
        response = self.client.get("/login")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_static(self):
        response = self.client.get("/static/favicon.ico")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(IS_CLOSED=True)
    def test_site_settings_is_closed_featured_file(self):
        response = self.client.get("/file/featured/test.txt")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(
        IS_CLOSED=False,
        WALLED_GARDEN_BY_IP_ENABLED=True,
        WHITELISTED_IP_RANGES=['10.10.10.10']
    )
    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted(self):
        response = self.client.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(
        IS_CLOSED=False,
        WALLED_GARDEN_BY_IP_ENABLED=True,
        WHITELISTED_IP_RANGES=['10.10.10.11/32']
    )
    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_different_ip(self):
        response = self.client.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateUsed(response, 'registration/login.html')

    @override_config(
        IS_CLOSED=False,
        WALLED_GARDEN_BY_IP_ENABLED=True,
        WHITELISTED_IP_RANGES=['10.10.10.0/24']
    )
    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_large_network(self):
        response = self.client.get("/981random3", HTTP_X_FORWARDED_FOR='10.10.10.108')

        self.assertTemplateNotUsed(response, 'registration/login.html')

    @override_config(
        IS_CLOSED=False,
        WALLED_GARDEN_BY_IP_ENABLED=True,
        WHITELISTED_IP_RANGES=['10.10.11.0/24']
    )
    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_large_network_different_range(self):
        response = self.client.get("/981random3", HTTP_X_FORWARDED_FOR='10.10.10.108')

        self.assertTemplateUsed(response, 'registration/login.html')

    @override_config(
        IS_CLOSED=False,
        WALLED_GARDEN_BY_IP_ENABLED=False,
        WHITELISTED_IP_RANGES=[]
    )
    def test_site_settings_is_not_walled_garden_by_ip_enabled_but_whitelisted(self):
        response = self.client.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateNotUsed(response, 'registration/login.html')


class TestSiteSettingsJavascriptSection(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.AUTHENTICATED_UUID = str(uuid.uuid4())
        self.ANONYMOUS_UUID = str(uuid.uuid4())


    def test_anonymous(self):
        with override_config(
            IS_CLOSED=False,
            STARTPAGE='cms',
            STARTPAGE_CMS=self.AUTHENTICATED_UUID,
            ANONYMOUS_START_PAGE='cms',
            ANONYMOUS_START_PAGE_CMS=self.ANONYMOUS_UUID,
        ):
            response = self.client.get('')
            content = response.content.decode()

        self.assertNotIn(self.AUTHENTICATED_UUID, content)
        self.assertIn(self.ANONYMOUS_UUID, content)

    def test_authenticated_user(self):
        with override_config(
            IS_CLOSED=False,
            STARTPAGE='cms',
            STARTPAGE_CMS=self.AUTHENTICATED_UUID,
            ANONYMOUS_START_PAGE='cms',
            ANONYMOUS_START_PAGE_CMS=self.ANONYMOUS_UUID,
        ):
            self.client.force_login(self.authenticated_user)
            response = self.client.get('')
            content = response.content.decode()

        self.assertIn(self.AUTHENTICATED_UUID, content)
        self.assertNotIn(self.ANONYMOUS_UUID, content)


class TestSiteSettingsProperties(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory()
        self.query = """
        query SiteGeneralSettings {
            siteSettings {
                %s
            }
        }
        """

    def test_site_plan(self):
        self.override_config(SITE_PLAN='foo')
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(self.query % 'sitePlan', {})
        self.assertEqual(response['data']['siteSettings']['sitePlan'], 'foo')

    def test_support_contract_enabled(self):
        self.override_config(SUPPORT_CONTRACT_ENABLED=True)
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(self.query % 'supportContractEnabled', {})
        self.assertEqual(response['data']['siteSettings']['supportContractEnabled'], True)

    def test_support_contract_hours(self):
        self.override_config(SUPPORT_CONTRACT_HOURS_REMAINING='9.2')
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(self.query % 'supportContractHoursRemaining', {})
        self.assertEqual(response['data']['siteSettings']['supportContractHoursRemaining'], 9.2)

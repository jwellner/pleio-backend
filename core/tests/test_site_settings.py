from django.db import connection
from django_tenants.test.cases import FastTenantTestCase, TenantTestCase
from django_tenants.test.client import TenantClient
from django.test import override_settings, Client
from core.models import Group, Comment, ProfileField
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from core.models import Group, Comment, ProfileField, SiteInvitation, SiteAccessRequest
from user.models import User
from blog.models import Blog
from cms.models import Page
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.core.cache import cache
from django.template.loader import render_to_string
from mixer.backend.django import mixer
from notifications.signals import notify
from core.lib import get_language_options


class SiteSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.user = mixer.blend(User, is_delete_requested=False)
        self.admin = mixer.blend(User, roles=['ADMIN'], is_delete_requested=False)
        self.delete_user = mixer.blend(User, is_delete_requested=True)
        self.anonymousUser = AnonymousUser()
        self.cmsPage1 = mixer.blend(Page, title="Z title")
        self.cmsPage2 = mixer.blend(Page, title="A title")
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')
        self.siteInvitation = mixer.blend(SiteInvitation, email='a@a.nl')
        self.siteAccessRequest = mixer.blend(SiteAccessRequest, email='b@b.nl', name='b')

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
                }
            }
        """

    def tearDown(self):
        self.siteInvitation.delete()
        self.cmsPage1.delete()
        self.cmsPage2.delete()
        self.profileField1.delete()
        self.profileField2.delete()
        self.admin.delete()
        self.user.delete()


    def test_site_settings_by_admin(self):

        request = HttpRequest()
        request.user = self.admin

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["siteSettings"]["name"], "Pleio 2.0")
        self.assertEqual(data["siteSettings"]["language"], "nl")
        self.assertEqual(data["siteSettings"]["extraLanguages"], [])
        self.assertEqual(data["siteSettings"]["languageOptions"], get_language_options())
        self.assertEqual(data["siteSettings"]["isClosed"], False)
        self.assertEqual(data["siteSettings"]["allowRegistration"], True)
        self.assertEqual(data["siteSettings"]["directRegistrationDomains"], [])
        self.assertEqual(data["siteSettings"]["defaultAccessIdOptions"], [{'value': 0, 'label': 'Alleen eigenaar'}, {'value': 1, 'label': 'Ingelogde gebruikers'}, {'value': 2, 'label': 'Iedereen (publiek zichtbaar)'}])
        self.assertEqual(data["siteSettings"]["defaultAccessId"], 1)
        self.assertEqual(data["siteSettings"]["googleAnalyticsId"], "")
        self.assertEqual(data["siteSettings"]["googleSiteVerification"], "")
        self.assertEqual(data["siteSettings"]["searchEngineIndexingEnabled"], False)
        self.assertEqual(data["siteSettings"]["piwikUrl"], "https://stats.pleio.nl/")
        self.assertEqual(data["siteSettings"]["piwikId"], "")

        self.assertEqual(data["siteSettings"]["themeOptions"], [{"value": 'leraar', 'label': 'Standaard'}, {'value': 'rijkshuisstijl', 'label': 'Rijkshuisstijl'}])
        self.assertEqual(data["siteSettings"]["fontOptions"], [
            {"value": "Arial", "label": "Arial"},
            {"value": "Open Sans", "label": "Open Sans"},
            {"value": "PT Sans", "label": "PT Sans"},
            {"value": "Rijksoverheid Sans", "label": "Rijksoverheid Sans"},
            {"value": "Roboto", "label": "Roboto"},
            {"value": "Source Sans Pro", "label": "Source Sans Pro"}
            ]
        )

        self.assertEqual(data["siteSettings"]["font"], "Rijksoverheid Sans")
        self.assertEqual(data["siteSettings"]["colorHeader"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorPrimary"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorSecondary"], "#009ee3")
        self.assertEqual(data["siteSettings"]["theme"], "leraar")
        self.assertEqual(data["siteSettings"]["logo"], "")
        self.assertEqual(data["siteSettings"]["logoAlt"], "")
        self.assertEqual(data["siteSettings"]["favicon"], "")
        self.assertEqual(data["siteSettings"]["likeIcon"], "heart")

        self.assertEqual(data["siteSettings"]["startPageOptions"], [{"value": "activity", "label": "Activiteitenstroom"},{"value": "cms", "label": "CMS pagina"}])
        self.assertEqual(data["siteSettings"]["startPage"], "activity")
        self.assertEqual(data["siteSettings"]["startPageCmsOptions"], [
            {"value": self.cmsPage2.guid, 'label': self.cmsPage2.title},
            {"value": self.cmsPage1.guid, 'label': self.cmsPage1.title}
        ])
        self.assertEqual(data["siteSettings"]["startPageCms"], "")
        self.assertEqual(data["siteSettings"]["showIcon"], False)
        self.assertIn("/static/icon", data["siteSettings"]["icon"]) # show default'':
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
        self.assertEqual(data["siteSettings"]["profileFields"], [{"key": self.profileField1.key}, {"key": self.profileField2.key}])

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
        self.assertEqual(data["siteSettings"]["siteInvites"]["edges"][0]['email'], 'a@a.nl')
        self.assertEqual(data["siteSettings"]["cookieConsent"], False)
        self.assertEqual(data["siteSettings"]["roleOptions"], [{'value': 'ADMIN', 'label': 'Beheerder'}, {'value': 'EDITOR', 'label': 'Redacteur'}, {'value': 'QUESTION_MANAGER', 'label': 'Vraagexpert'}])
        self.assertEqual(data["siteSettings"]["siteAccessRequests"]["edges"][0]['email'], 'b@b.nl')
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


    def test_site_settings_by_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
        }

        self.query = """
            query SiteGeneralSettings {
                siteSettings {
                    language
                }
            }
        """
        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_site_settings_by_user(self):

        request = HttpRequest()
        request.user = self.user

        variables = {
        }

        self.query = """
            query SiteGeneralSettings {
                siteSettings {
                    language
                }
            }
        """
        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


class SiteSettingsIsClosedTestCase(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.c = TenantClient(self.tenant)
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), True)

    def tearDown(self):
        cache.clear()

    def test_site_settings_is_closed_random(self):
        response = self.c.get("/981random3")
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_graphql(self):
        response = self.c.get("/graphql")
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_robots(self):
        response = self.c.get("/robots.txt")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_sitemap(self):
        response = self.c.get("/sitemap.xml")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_oidc(self):
        response = self.c.get("/oidc/test")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_login(self):
        response = self.c.get("/login")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_static(self):
        response = self.c.get("/static/favicon.ico")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_closed_featured_file(self):
        response = self.c.get("/file/featured/test.txt")
        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WALLED_GARDEN_BY_IP_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'WHITELISTED_IP_RANGES'), ['10.10.10.10'])

        response = self.c.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_different_ip(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WALLED_GARDEN_BY_IP_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'WHITELISTED_IP_RANGES'), ['10.10.10.11/32'])

        response = self.c.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateUsed(response, 'registration/login.html')

    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_large_network(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WALLED_GARDEN_BY_IP_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'WHITELISTED_IP_RANGES'), ['10.10.10.0/24'])

        response = self.c.get("/981random3", HTTP_X_FORWARDED_FOR='10.10.10.108')

        self.assertTemplateNotUsed(response, 'registration/login.html')

    def test_site_settings_is_walled_garden_by_ip_enabled_but_whitelisted_large_network_different_range(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WALLED_GARDEN_BY_IP_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'WHITELISTED_IP_RANGES'), ['10.10.11.0/24'])

        response = self.c.get("/981random3", HTTP_X_FORWARDED_FOR='10.10.10.108')

        self.assertTemplateUsed(response, 'registration/login.html')

    def test_site_settings_is_not_walled_garden_by_ip_enabled_but_whitelisted(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WALLED_GARDEN_BY_IP_ENABLED'), False)
        cache.set("%s%s" % (connection.schema_name, 'WHITELISTED_IP_RANGES'), [])

        response = self.c.get("/981random3", REMOTE_ADDR='10.10.10.10')

        self.assertTemplateNotUsed(response, 'registration/login.html')
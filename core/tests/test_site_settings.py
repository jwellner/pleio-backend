from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from core.models import Group, Comment, ProfileField
from user.models import User
from blog.models import Blog
from cms.models import Page
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from notifications.signals import notify


class SiteSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.anonymousUser = AnonymousUser()
        self.cmsPage1 = mixer.blend(Page, title="Z title")
        self.cmsPage2 = mixer.blend(Page, title="A title")
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')

        self.query = """
            query SiteGeneralSettings {
                siteSettings {
                    languageOptions {
                        value
                        label
                    }
                    language
                    name
                    description
                    isClosed
                    allowRegistration
                    defaultAccessIdOptions {
                        value
                        label
                    }
                    defaultAccessId
                    googleAnalyticsUrl
                    googleSiteVerification
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
                        }
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

                    showLoginRegister
                    customTagsAllowed
                    showUpDownVoting
                    enableSharing
                    showViewsCount
                    newsletter
                    cancelMembershipEnabled
                    advancedPermissions
                    showExcerptInNewsCard
                    commentsOnNews
                    eventExport
                    questionerCanChooseBestAnswer
                    statusUpdateGroups
                    subgroups
                    groupMemberExport
                }
            }
        """

    def tearDown(self):
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
        self.assertEqual(data["siteSettings"]["description"], "Omschrijving site")
        self.assertEqual(data["siteSettings"]["languageOptions"], [{'value': 'nl', 'label': 'Nederlands'}, {'value': 'en', 'label': 'Engels'}])
        self.assertEqual(data["siteSettings"]["isClosed"], False)
        self.assertEqual(data["siteSettings"]["allowRegistration"], True)
        self.assertEqual(data["siteSettings"]["defaultAccessIdOptions"], [{'value': 0, 'label': 'Alleen mijzelf'}, {'value': 1, 'label': 'Ingelogde gebruikers'}, {'value': 2, 'label': 'Iedereen publiek zichtbaar'}])
        self.assertEqual(data["siteSettings"]["defaultAccessId"], 1)
        self.assertEqual(data["siteSettings"]["googleAnalyticsUrl"], "")
        self.assertEqual(data["siteSettings"]["googleSiteVerification"], "")
        self.assertEqual(data["siteSettings"]["piwikUrl"], "")
        self.assertEqual(data["siteSettings"]["piwikId"], "")

        self.assertEqual(data["siteSettings"]["themeOptions"], [{"value": 'leraar', 'label': 'Standaard'}, {'value': 'rijkshuisstijl', 'label': 'Rijkshuisstijl'}])
        self.assertEqual(data["siteSettings"]["fontOptions"], [{"value": "Rijksoverheid Sans", "label": "Rijksoverheid Sans"},{"value": "Roboto", "label": "Roboto"},{"value": "Source Sans Pro", "label": "Source Sans Pro"}])
        self.assertEqual(data["siteSettings"]["font"], "Rijksoverheid Sans")
        self.assertEqual(data["siteSettings"]["colorHeader"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorPrimary"], "#0e2f56")
        self.assertEqual(data["siteSettings"]["colorSecondary"], "#009ee3")
        self.assertEqual(data["siteSettings"]["theme"], "leraar")
        self.assertEqual(data["siteSettings"]["logo"], "")
        self.assertEqual(data["siteSettings"]["logoAlt"], "")
        self.assertEqual(data["siteSettings"]["likeIcon"], "heart")

        self.assertEqual(data["siteSettings"]["startPageOptions"], [{"value": "activity", "label": "Activiteitenstroom"},{"value": "cms", "label": "CMS pagina"}])
        self.assertEqual(data["siteSettings"]["startPage"], "activity")
        self.assertEqual(data["siteSettings"]["startPageCmsOptions"], [
            {"value": self.cmsPage2.guid, 'label': self.cmsPage2.title},
            {"value": self.cmsPage1.guid, 'label': self.cmsPage1.title}
        ])
        self.assertEqual(data["siteSettings"]["startPageCms"], "")
        self.assertEqual(data["siteSettings"]["showIcon"], False)
        self.assertIn("/static/icon", data["siteSettings"]["icon"]) # show default
        self.assertEqual(data["siteSettings"]["menu"], [
            {"link": "/blog", "title": "Blog", "children": []},
            {"link": "/news", "title": "Nieuws", "children": []},
            {"link": "/groups", "title": "Groepen", "children": []},
            {"link": "/questions", "title": "Vragen", "children": []},
            {"link": "/wiki", "title": "Wiki", "children": []}
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

        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["field_type"], "userField")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["field"], "guid")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][0]["label"], "guid")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["field_type"], "userField")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["field"], "banned")
        self.assertEqual(data["siteSettings"]["exportableUserFields"][6]["label"], "banned")

        self.assertEqual(data["siteSettings"]["showLoginRegister"], True)
        self.assertEqual(data["siteSettings"]["customTagsAllowed"], True)
        self.assertEqual(data["siteSettings"]["showUpDownVoting"], True)
        self.assertEqual(data["siteSettings"]["enableSharing"], True)
        self.assertEqual(data["siteSettings"]["showViewsCount"], True)
        self.assertEqual(data["siteSettings"]["newsletter"], False)
        self.assertEqual(data["siteSettings"]["cancelMembershipEnabled"], True)
        self.assertEqual(data["siteSettings"]["advancedPermissions"], False)
        self.assertEqual(data["siteSettings"]["showExcerptInNewsCard"], False)
        self.assertEqual(data["siteSettings"]["commentsOnNews"], False)
        self.assertEqual(data["siteSettings"]["eventExport"], False)
        self.assertEqual(data["siteSettings"]["questionerCanChooseBestAnswer"], False)
        self.assertEqual(data["siteSettings"]["statusUpdateGroups"], True)
        self.assertEqual(data["siteSettings"]["subgroups"], False)
        self.assertEqual(data["siteSettings"]["groupMemberExport"], False)


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

from django.db import connection
from django.core.files import File
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from django.conf import settings
from ariadne import graphql_sync
import json
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Widget, Setting, ProfileField
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import patch, MagicMock

class EditSiteSettingTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')
        self.profileField3 = ProfileField.objects.create(key='text_key3', name='text_name', field_type='text_field')
        self.profileField4 = ProfileField.objects.create(key='text_key4', name='text_name', field_type='text_field')


    def tearDown(self):
        self.admin.delete()
        self.profileField1.delete()
        self.profileField2.delete()
        self.profileField3.delete()
        self.profileField4.delete()
        self.user.delete()

        Setting.objects.all().delete()
        cache.clear()

    def test_edit_site_setting_by_admin(self):
        mutation = """
            mutation EditSiteSetting($input: editSiteSettingInput!) {
                editSiteSetting(input: $input) {
                    siteSettings {
                        language
                        name
                        description
                        isClosed
                        allowRegistration
                        defaultAccessId
                        defaultAccessIdOptions {
                            value
                            label
                        }
                        googleAnalyticsId
                        googleSiteVerification

                        piwikUrl
                        piwikId

                        theme
                        logoAlt
                        likeIcon
                        font
                        colorPrimary
                        colorSecondary
                        colorHeader

                        startPage
                        startPageCms
                        showIcon
                        icon
                        menu {
                            title
                            link
                            children {
                                title
                                link
                                children {
                                    title
                                }
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
                            isFilter
                            isInOverview
                        }

                        profileSections {
                            name
                            profileFieldGuids
                        }

                        tagCategories {
                            name
                            values
                        }
                        showTagsInFeed
                        showTagsInDetail

                        defaultEmailOverviewFrequency
                        emailOverviewSubject
                        emailOverviewTitle
                        emailOverviewIntro
                        emailNotificationShowExcerpt

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

                        onboardingEnabled
                        onboardingForceExistingUsers
                        onboardingIntro
                        cookieConsent
                    }
                }
            }
        """
        variables = {
            "input": {
                "language": "en",
                "name": "name2",
                "description": "description2",
                "isClosed": True,
                "allowRegistration": False,
                "defaultAccessId": 0,
                "googleAnalyticsId": "123",
                "googleSiteVerification": "code1",

                "piwikUrl": "url3",
                "piwikId": "id1",

                "theme": "rijkshuisstijl",
                "logoAlt": "alttext1",
                "likeIcon": "thumbs",
                "font": "Roboto",
                "colorPrimary": "#111111",
                "colorSecondary": "#222222",
                "colorHeader": "#333333",

                "startPage": "cms",
                "startPageCms": "123456",
                "showIcon": True,
                # TODO: "icon": "",
                "menu": [{"id": 1, "link": "/news", "parentId": None, "title": "Nieuws"}, {"id": 2, "link": "/blog", "parentId": 1, "title": "Blog"}],

                "numberOfFeaturedItems": 3,
                "enableFeedSorting": True,
                "showExtraHomepageFilters": False,
                "showLeader": True,
                "showLeaderButtons": True,
                "subtitle": "subtitle1",
                "leaderImage": "https://test1.nl",
                "showInitiative": True,
                "initiativeTitle": "intitle1",
                "initiativeDescription": "indescription1",
                "initiativeImage": "https://test2.nl",
                "initiativeImageAlt": "inimagealt1",
                "initiativeLink": "https://link.nl",

                "directLinks": [{"title":"extern","link":"https://nos.nl"},{"title":"intern","link":"/news"},{"title":"intern lang","link":"https://nieuw-template.pleio-test.nl/news"}],
                "footer": [{"link":"https://www.nieuw.nl","title":"Nieuwe link"},{"link":"https://wnas.nl","title":"wnas"}],

                "profile": [{"isFilter": False, "isInOverview": False, "key": "key1", "name": "name1"},
                            {"isFilter": False, "isInOverview": False, "key": "key2", "name": "name2"},
                            {"isFilter": True, "isInOverview": True, "key": "key3", "name": "name3"}],

                "profileSections": [{"name": "section_one", "profileFieldGuids": [str(self.profileField1.id), str(self.profileField3.id)]},
                                    {"name": "section_two", "profileFieldGuids": [str(self.profileField4.id)]},
                                    {"name": "section_three", "profileFieldGuids": []}],

                "tagCategories": [{"name": "cat1", "values": ["tag1", "tag2"]},
                                  {"name": "cat2", "values": ["tag3", "tag4"]}],
                'showTagsInFeed': True,
                'showTagsInDetail': True,

                "defaultEmailOverviewFrequency": "monthly",
                "emailOverviewSubject": "emailOverviewSubject1",
                "emailOverviewTitle": "emailOverviewTitle1",
                "emailOverviewIntro": "emailOverviewIntro1",
                "emailNotificationShowExcerpt": True,

                'showLoginRegister': False,
                'customTagsAllowed': False,
                'showUpDownVoting': False,
                'enableSharing': False,
                'showViewsCount': False,
                'newsletter': True,
                'cancelMembershipEnabled': False,
                'advancedPermissions': True,
                'showExcerptInNewsCard': True,
                'commentsOnNews': True,
                'eventExport': True,
                'questionerCanChooseBestAnswer': True,
                'statusUpdateGroups': False,
                'subgroups': True,
                'groupMemberExport': True,

                'onboardingEnabled': True,
                'onboardingForceExistingUsers': True,
                'onboardingIntro': 'Welcome onboarding',

                'cookieConsent': True

            }
        }

        request = HttpRequest()
        request.user = self.admin
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["language"], "en")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["name"], "name2")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["description"], "description2")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["isClosed"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["allowRegistration"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["defaultAccessId"], 0)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["defaultAccessIdOptions"], [{'value': 0, 'label': 'Alleen mijzelf'}, {'value': 1, 'label': 'Ingelogde gebruikers'}])
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["googleAnalyticsId"], "123")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["googleSiteVerification"], "code1")

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["piwikUrl"], "url3")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["piwikId"], "id1")

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["theme"], "rijkshuisstijl")
        # TODO: self.assertEqual(data["editSiteSetting"]["siteSettings"]["logo"], "id1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["logoAlt"], "alttext1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["likeIcon"], "thumbs")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["font"], "Roboto")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["colorPrimary"], "#111111")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["colorSecondary"], "#222222")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["colorHeader"], "#333333")

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["startPage"], "cms")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["startPageCms"], "123456")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showIcon"], True)
        # TODO: self.assertEqual(data["editSiteSetting"]["siteSettings"]["icon"], "heart")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["menu"], [{"title": "Nieuws", "link": "/news", "children": [
            {"title": "Blog", "link": "/blog", "children": []}
        ]}])

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["numberOfFeaturedItems"], 3)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["enableFeedSorting"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showExtraHomepageFilters"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showLeader"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showLeaderButtons"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["subtitle"], "subtitle1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["leaderImage"], "https://test1.nl")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showInitiative"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["initiativeTitle"], "intitle1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["initiativeDescription"], "indescription1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["initiativeImage"], "https://test2.nl")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["initiativeImageAlt"], "inimagealt1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["initiativeLink"], "https://link.nl")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["directLinks"], [{"title":"extern","link":"https://nos.nl"},{"title":"intern","link":"/news"},{"title":"intern lang","link":"https://nieuw-template.pleio-test.nl/news"}])
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["footer"], [{"title":"Nieuwe link","link":"https://www.nieuw.nl"},{"title":"wnas","link":"https://wnas.nl"}])

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["profile"], [{"isFilter": False, "isInOverview": False, "key": "key1", "name": "name1"},
                                                                              {"isFilter": False, "isInOverview": False, "key": "key2", "name": "name2"},
                                                                              {"isFilter": True, "isInOverview": True, "key": "key3", "name": "name3"}])

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["profileSections"], [{"name": "section_one", "profileFieldGuids": [str(self.profileField1.id), str(self.profileField3.id)]},
                                                                                      {"name": "section_two", "profileFieldGuids": [str(self.profileField4.id)]},
                                                                                      {"name": "section_three", "profileFieldGuids": []}])

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["tagCategories"], [{"name": "cat1", "values": ["tag1", "tag2"]},
                                                                                    {"name": "cat2", "values": ["tag3", "tag4"]}])
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showTagsInFeed"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showTagsInDetail"], True)

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["defaultEmailOverviewFrequency"], "monthly")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["emailOverviewSubject"], "emailOverviewSubject1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["emailOverviewTitle"], "emailOverviewTitle1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["emailOverviewIntro"], "emailOverviewIntro1")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["emailNotificationShowExcerpt"], True)

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showLoginRegister"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["customTagsAllowed"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showUpDownVoting"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["enableSharing"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showViewsCount"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["newsletter"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["cancelMembershipEnabled"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["advancedPermissions"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["showExcerptInNewsCard"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["commentsOnNews"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["eventExport"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["questionerCanChooseBestAnswer"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["statusUpdateGroups"], False)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["subgroups"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["groupMemberExport"], True)

        self.assertEqual(data["editSiteSetting"]["siteSettings"]["onboardingEnabled"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["onboardingForceExistingUsers"], True)
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["onboardingIntro"], "Welcome onboarding")
        self.assertEqual(data["editSiteSetting"]["siteSettings"]["cookieConsent"], True)

    @patch("file.models.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_edit_site_setting_logo_and_icon(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'logo.png'
        file_mock.content_type = 'image/png'
        file_mock.id = 'a12'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation EditSiteSetting($input: editSiteSettingInput!) {
                editSiteSetting(input: $input) {
                    siteSettings {
                        logo
                        icon
                    }
                }
            }
        """

        variables = {
            "input": {
                "logo": "image.png",
                "icon": "image.png"
            }
        }

        request = HttpRequest()
        request.user = self.admin
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertIsNotNone(data["editSiteSetting"]["siteSettings"]["logo"])
        self.assertIsNotNone(data["editSiteSetting"]["siteSettings"]["icon"])


    def test_edit_site_setting_by_anonymous(self):
        mutation = """
            mutation EditSiteSetting($input: editSiteSettingInput!) {
                editSiteSetting(input: $input) {
                    siteSettings {
                        language
                    }
                }
            }
        """

        variables = {
            "input": {
                "language": "en"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        result = graphql_sync(schema, { "query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_edit_site_setting_by_user(self):
        mutation = """
            mutation EditSiteSetting($input: editSiteSettingInput!) {
                editSiteSetting(input: $input) {
                    siteSettings {
                        language
                    }
                }
            }
        """

        variables = {
            "input": {
                "language": "en"
            }
        }

        request = HttpRequest()
        request.user = self.user
        result = graphql_sync(schema, { "query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")

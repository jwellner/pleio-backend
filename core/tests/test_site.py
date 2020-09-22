from django_tenants.test.cases import FastTenantTestCase
from core import config
from user.models import User
from backend2.schema import schema
from ariadne import graphql_sync
from mixer.backend.django import mixer
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest


class SiteTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.anonymousUser = AnonymousUser()

        self.query = """
            query testSite {
                site {
                    guid
                    name
                    theme
                    menu {
                        title
                        link
                        children {
                            title
                            link
                        }
                    }
                    profile {
                        key
                        name
                        fieldType
                        isFilter
                        isFilterable
                    }
                    achievementsEnabled
                    cancelMembershipEnabled
                    footer {
                        title
                        link
                    }
                    directLinks {
                        title
                        link
                    }
                    accessIds {
                        id
                        description
                    }
                    defaultAccessId
                    language
                    logo
                    logoAlt
                    icon
                    iconAlt
                    showIcon
                    startpage
                    showLeader
                    showLeaderButtons
                    subtitle
                    leaderImage
                    showInitiative
                    initiativeTitle
                    initiativeImage
                    initiativeImageAlt
                    initiativeDescription
                    initiatorLink
                    style {
                        font
                        colorPrimary
                        colorSecondary
                        colorHeader
                    }
                    customTagsAllowed
                    tagCategories {
                        values
                    }
                    activityFilter {
                        contentTypes {
                            key
                            value
                        }
                    }
                    showExtraHomepageFilters
                    showTagsInFeed
                    showTagsInDetail
                    usersOnline
                }
            }
        """

    def tearDown(self):
        self.user.delete()


    def test_site(self):

        request = HttpRequest()
        request.user = self.user

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["site"]["name"], config.NAME)
        self.assertEqual(data["site"]["guid"], "1")
        self.assertEqual(data["site"]["theme"], config.THEME)
        self.assertEqual(data["site"]["menu"], config.MENU)
        self.assertEqual(data["site"]["style"]["font"], config.FONT)
        self.assertEqual(data["site"]["style"]["colorPrimary"], config.COLOR_PRIMARY)
        self.assertEqual(data["site"]["style"]["colorSecondary"], config.COLOR_SECONDARY)
        self.assertEqual(data["site"]["showTagsInFeed"], config.SHOW_TAGS_IN_FEED)
        self.assertEqual(data["site"]["showTagsInDetail"], config.SHOW_TAGS_IN_DETAIL)


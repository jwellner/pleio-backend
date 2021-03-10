from django_tenants.test.cases import FastTenantTestCase
from core import config
from user.models import User
from core.models import ProfileField
from backend2.schema import schema
from ariadne import graphql_sync
from mixer.backend.django import mixer
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.core.cache import cache
from django.db import connection

class SiteTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.anonymousUser = AnonymousUser()

        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='date_field')

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
                    profileFields {
                        key
                        name
                        value
                        category
                        fieldType
                    }
                }
            }
        """

    def tearDown(self):
        self.user.delete()

        self.profileField1.delete()
        self.profileField2.delete()

    def test_site(self):

        request = HttpRequest()
        request.user = self.user

        variables = {
        }

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

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
        self.assertEqual(data["site"]["accessIds"], [
            {'id': 0, 'description': 'Alleen eigenaar'},
            {'id': 1, 'description': 'Ingelogde gebruikers'},
            {'id': 2, 'description': 'Iedereen (publiek zichtbaar)'},
        ])

        self.assertEqual(data["site"]["profileFields"][0]["key"], self.profileField1.key)
        self.assertEqual(data["site"]["profileFields"][1]["fieldType"], "dateField")

    def test_site_closed(self):

        request = HttpRequest()
        request.user = self.user

        variables = {
        }

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), True)

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["site"]["accessIds"], [
            {'id': 0, 'description': 'Alleen eigenaar'},
            {'id': 1, 'description': 'Ingelogde gebruikers'},
        ])

from core import config, override_local_config
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.models import ProfileField
from mixer.backend.django import mixer
from django.core.cache import cache
from django.db import connection


class SiteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)

        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='date_field')

        self.override_config(PROFILE_SECTIONS=[{"name": "section_one", "profileFieldGuids": [self.profileField1.guid, self.profileField2.guid]}])
        self.override_config(COLLAB_EDITING_ENABLED=True)
        self.override_config(BLOCKED_USER_INTRO_MESSAGE="another blockedUserIntroMessage")

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
                            accessId
                        }
                        accessId
                    }
                    menuState
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
                        category
                        fieldType
                    }
                    editUserNameEnabled
                    commentWithoutAccountEnabled
                    questionLockAfterActivity
                    questionLockAfterActivityLink
                    maxCharactersInAbstract
                    showSuggestedItems
                    collabEditingEnabled
                    preserveFileExif
                    scheduleAppointmentEnabled
                    videocallEnabled
                    videocallProfilepage
                    blockedUserIntroMessage
                }
            }
        """

    def tearDown(self):
        self.user.delete()
        self.profileField1.delete()
        self.profileField2.delete()
        cache.clear()
        super().tearDown()

    def test_site(self):
        self.override_config(IS_CLOSED=False)

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["site"]["name"], config.NAME)
        self.assertEqual(data["site"]["guid"], "1")
        self.assertEqual(data["site"]["theme"], config.THEME)
        self.assertEqual(data["site"]["menu"], config.MENU)
        self.assertEqual(data["site"]["menuState"], config.MENU_STATE)
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
        self.assertEqual(data["site"]["editUserNameEnabled"], config.EDIT_USER_NAME_ENABLED)
        self.assertEqual(data["site"]["commentWithoutAccountEnabled"], config.COMMENT_WITHOUT_ACCOUNT_ENABLED)
        self.assertEqual(data["site"]["questionLockAfterActivity"], config.QUESTION_LOCK_AFTER_ACTIVITY)
        self.assertEqual(data["site"]["questionLockAfterActivityLink"], config.QUESTION_LOCK_AFTER_ACTIVITY_LINK)
        self.assertEqual(data["site"]["maxCharactersInAbstract"], config.MAX_CHARACTERS_IN_ABSTRACT)
        self.assertEqual(data["site"]["showSuggestedItems"], config.SHOW_SUGGESTED_ITEMS)
        self.assertEqual(data["site"]["collabEditingEnabled"], config.COLLAB_EDITING_ENABLED)
        self.assertEqual(data["site"]["preserveFileExif"], config.PRESERVE_FILE_EXIF)
        self.assertEqual(data["site"]["blockedUserIntroMessage"], config.BLOCKED_USER_INTRO_MESSAGE)

    def test_site_closed(self):
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), True)

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["site"]["accessIds"], [
            {'id': 0, 'description': 'Alleen eigenaar'},
            {'id': 1, 'description': 'Ingelogde gebruikers'},
        ])

    @override_local_config(ONLINEAFSPRAKEN_ENABLED=True)
    def test_schedule_appointment_enabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['scheduleAppointmentEnabled'], True)

    @override_local_config(ONLINEAFSPRAKEN_ENABLED=False)
    def test_schedule_appointment_disabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['scheduleAppointmentEnabled'], False)

    @override_local_config(VIDEOCALL_ENABLED=True)
    def test_videocall_enabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallEnabled'], True)

    @override_local_config(VIDEOCALL_ENABLED=False)
    def test_videocall_disabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallEnabled'], False)

    @override_local_config(VIDEOCALL_PROFILEPAGE=True)
    def test_videocall_profilepage_enabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallProfilepage'], True)

    @override_local_config(VIDEOCALL_PROFILEPAGE=False)
    def test_videocall_profilepage_enabled(self):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallProfilepage'], False)

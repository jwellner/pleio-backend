from core import config, override_local_config
from core.tests.helpers import PleioTenantTestCase, override_config
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

        self.PROFILE_SECTIONS = [{"name": "section_one", "profileFieldGuids": [self.profileField1.guid, self.profileField2.guid]}]

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
                    entityFilter {
                        contentTypes {
                            key
                            value
                        }
                    }
                    searchFilter {
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
                    pageTagFilters(contentType: "blog") {
                        contentType
                        showTagFilter
                        showTagCategories
                    }
                    recurringEventsEnabled
                }
            }
        """

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_site(self):

        with override_config(
            IS_CLOSED=False,
            COLLAB_EDITING_ENABLED=True,
            PROFILE_SECTIONS=self.PROFILE_SECTIONS,
            BLOCKED_USER_INTRO_MESSAGE="another blockedUserIntroMessage",
            PAGE_TAG_FILTERS=[
                {'showTagFilter': False, 'showTagCategories': [], 'contentType': 'blog'},
                {'showTagFilter': False, 'showTagCategories': [], 'contentType': 'news'}
            ]
        ):
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

            self.assertDictEqual(data['site']['activityFilter'], {
                "contentTypes": [
                    {'key': 'blog', 'value': 'Blog'},
                    {'key': 'page', 'value': 'Tekst pagina'},
                    {'key': 'discussion', 'value': 'Discussie'},
                    {'key': 'event', 'value': 'Agenda-item'},
                    {'key': 'news', 'value': 'Nieuws'},
                    {'key': 'question', 'value': 'Vraag'},
                    {'key': 'wiki', 'value': 'Wiki'},
                    {'key': 'statusupdate', 'value': 'Update'}
                ]
            })
            self.assertDictEqual(data['site']['entityFilter'], {
                "contentTypes": [
                    {'key': 'blog', 'value': 'Blog'},
                    {'key': 'page', 'value': 'Pagina'},
                    {'key': 'discussion', 'value': 'Discussie'},
                    {'key': 'event', 'value': 'Agenda-item'},
                    {'key': 'news', 'value': 'Nieuws'},
                    {'key': 'question', 'value': 'Vraag'},
                    {'key': 'wiki', 'value': 'Wiki'},
                    {'key': 'file', 'value': 'Bestand'},
                    {'key': 'folder', 'value': 'Map'},
                    {'key': 'pad', 'value': 'Pad'},
                ]
            })
            self.assertDictEqual(data['site']['searchFilter'], {
                "contentTypes": [
                    {'key': 'user', 'value': 'Gebruiker'},
                    {'key': 'group', 'value': 'Groep'},
                    {'key': 'blog', 'value': 'Blog'},
                    {'key': 'page', 'value': 'Pagina'},
                    {'key': 'discussion', 'value': 'Discussie'},
                    {'key': 'event', 'value': 'Agenda-item'},
                    {'key': 'news', 'value': 'Nieuws'},
                    {'key': 'question', 'value': 'Vraag'},
                    {'key': 'wiki', 'value': 'Wiki'},
                    {'key': 'file', 'value': 'Bestand'},
                    {'key': 'folder', 'value': 'Map'},
                    {'key': 'pad', 'value': 'Pad'},
                ]
            })
            self.assertEqual(data['site']['pageTagFilters'], {'showTagFilter': False, 'showTagCategories': [], 'contentType': 'blog'})
            self.assertEqual(data['site']["recurringEventsEnabled"], False)

    def test_site_closed(self):
        with override_config(
            IS_CLOSED=True,
        ):
            self.graphql_client.force_login(self.user)
            result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["site"]["accessIds"], [
            {'id': 0, 'description': 'Alleen eigenaar'},
            {'id': 1, 'description': 'Ingelogde gebruikers'},
        ])

    def test_schedule_appointment_enabled(self):
        with override_config(
            ONLINEAFSPRAKEN_ENABLED=True,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['scheduleAppointmentEnabled'], True)

    def test_schedule_appointment_disabled(self):
        with override_config(
            ONLINEAFSPRAKEN_ENABLED=False,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['scheduleAppointmentEnabled'], False)

    def test_videocall_enabled(self):
        with override_config(
            VIDEOCALL_ENABLED=True,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallEnabled'], True)

    def test_videocall_disabled(self):
        with override_config(
            VIDEOCALL_ENABLED=False,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallEnabled'], False)

    def test_videocall_profilepage_enabled(self):
        with override_config(
            VIDEOCALL_PROFILEPAGE=True,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallProfilepage'], True)

    def test_videocall_profilepage_disabled(self):
        with override_config(
            VIDEOCALL_PROFILEPAGE=False,
            IS_CLOSED=False,
        ):
            result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['site']['videocallProfilepage'], False)

    def test_recurring_events_enabled(self):
        self.query = """
            query SiteGeneralSettings {
                site {
                    recurringEventsEnabled
                }
            }
        """
        with override_config(
            RECURRING_EVENTS_ENABLED=True,
            IS_CLOSED=False,
        ):
            self.graphql_client.force_login(self.user)
            response = self.graphql_client.post(self.query, {})
            response = response['data']
        self.assertEqual(response['site']['recurringEventsEnabled'], True)

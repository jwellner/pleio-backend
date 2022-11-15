from unittest import mock

from core.models import VideoCall, VideoCallGuest
from core.tasks import create_notification
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMutationInitiateVideoCallTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        from core.resolvers.mutation_initiate_videocall import localtime
        self.time = localtime()
        self.mocked_localtime = mock.patch("core.resolvers.mutation_initiate_videocall.localtime").start()
        self.mocked_localtime.return_value = self.time

        self.host = UserFactory()
        self.guest = UserFactory()

        self.override_config(VIDEOCALL_ENABLED=True,
                             VIDEOCALL_PROFILEPAGE=True)

        self.HOST_URL = 'https://host/url/'
        self.GUEST_URL = 'https://guest/url/'

        self.create_notification = mock.patch("core.tasks.create_notification.delay").start()
        self.get_video_call_params = mock.patch("core.resolvers.mutation_initiate_videocall.get_video_call_params").start()
        self.get_video_call_params.return_value = {
            "VideoCallHostURL": self.HOST_URL,
            "VideoCallGuestURL": self.GUEST_URL,
        }

        self.query = '''
        mutation StartVideoCall($guid: String!) {
            test: initiateVideocall(userGuid: $guid){
                success
                guestUrl
                hostUrl
            }
        }
        '''

        self.variables = {
            "guid": self.guest.guid,
        }

    def tearDown(self):
        self.host.delete()
        self.guest.delete()

        super().tearDown()

    def test_invite_guest_user(self):
        self.graphql_client.force_login(self.host)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertEqual(result['data']['test']['success'], True)
        self.assertEqual(result['data']['test']['hostUrl'], self.HOST_URL)
        self.assertEqual(result['data']['test']['guestUrl'], self.GUEST_URL)
        self.assertDictEqual(self.get_video_call_params.call_args.args[0], {
            'date': self.time.date().isoformat(),
            'start_time': self.time.strftime("%H:%M"),
            'meeting_guest_name': self.guest.name,
            'meeting_host_name': self.host.name
        })

        video_call = VideoCall.objects.filter(user=self.host).first()
        self.assertTrue(video_call)
        self.assertEqual(video_call.recipients(), [self.host])

        guest_call = VideoCallGuest.objects.filter(user=self.guest).first()
        self.assertTrue(guest_call)
        self.assertEqual(guest_call.recipients(), [self.guest])

        self.assertEqual(self.create_notification.call_count, 2)
        self.assertEqual([c.kwargs for c in self.create_notification.call_args_list], [
            {'schema_name': self.tenant.schema_name,
             'verb': 'custom',
             'model_name': video_call._meta.label,
             'entity_id': video_call.guid,
             'sender_id': self.host.guid},
            {'schema_name': self.tenant.schema_name,
             'verb': 'custom',
             'model_name': guest_call._meta.label,
             'entity_id': guest_call.guid,
             'sender_id': self.host.guid},
        ])

    def test_limit_reached(self):
        self.override_config(VIDEOCALL_THROTTLE=1)
        video_call = VideoCall.objects.create(user=self.host,
                                              guest_url=self.GUEST_URL,
                                              host_url=self.HOST_URL)
        VideoCallGuest.objects.create(user=self.guest,
                                      video_call=video_call)

        with self.assertGraphQlError("videocall_limit_reached"):
            self.graphql_client.force_login(self.host)
            self.graphql_client.post(self.query, self.variables)


class TestCreateNotificationForVideoCallTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.override_config(VIDEOCALL_ENABLED=True,
                             VIDEOCALL_PROFILEPAGE=True)

        self.host = UserFactory()
        self.guest = UserFactory()

        self.HOST_URL = 'https://host/url/'
        self.GUEST_URL = 'https://guest/url/'

        self.vc_host = VideoCall.objects.create(
            user=self.host,
            host_url=self.HOST_URL,
            guest_url=self.GUEST_URL,
        )
        self.vc_guest = VideoCallGuest.objects.create(
            user=self.guest,
            video_call=self.vc_host,
        )

        self.host.notifications.all().mark_all_as_read()
        self.guest.notifications.all().mark_all_as_read()

        self.query = '''
        query GetNotifications($unread: Boolean) {
            test: notifications(unread: $unread){
                edges {
                    action
                    entity {
                        guid
                    }
                    customMessage
                }            
            }
        }
        '''
        self.variables = {
            'unread': True
        }

    def test_host_notification(self):
        create_notification(schema_name=self.tenant.schema_name,
                            verb='custom',
                            model_name=self.vc_host._meta.label,
                            entity_id=self.vc_host.guid,
                            sender_id=self.host.guid)

        self.graphql_client.force_login(self.host)
        result = self.graphql_client.post(self.query, self.variables)

        edges = result['data']['test']['edges']
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['action'], 'custom')
        self.assertEqual(edges[0]['entity'], None)
        self.assertIn(self.guest.name, edges[0]['customMessage'])
        self.assertNotIn(self.host.name, edges[0]['customMessage'])
        self.assertIn(self.HOST_URL, edges[0]['customMessage'])
        self.assertNotIn(self.GUEST_URL, edges[0]['customMessage'])

    def test_guest_notification(self):
        create_notification(schema_name=self.tenant.schema_name,
                            verb='custom',
                            model_name=self.vc_guest._meta.label,
                            entity_id=self.vc_guest.guid,
                            sender_id=self.host.guid)

        self.graphql_client.force_login(self.guest)
        result = self.graphql_client.post(self.query, self.variables)

        edges = result['data']['test']['edges']
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['action'], 'custom')
        self.assertEqual(edges[0]['entity'], None)
        self.assertNotIn(self.guest.name, edges[0]['customMessage'])
        self.assertIn(self.host.name, edges[0]['customMessage'])
        self.assertNotIn(self.HOST_URL, edges[0]['customMessage'])
        self.assertIn(self.GUEST_URL, edges[0]['customMessage'])

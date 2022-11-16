from core.models import VideoCall, VideoCallGuest
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestVideocallModelsTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.host = UserFactory()
        self.guest1 = UserFactory()
        self.guest2 = UserFactory()
        self.guest3 = UserFactory()
        self.video_call = VideoCall.objects.create(
            user=self.host,
            host_url="https://host/url/",
            guest_url="https://guest/url/"
        )

    def tearDown(self):
        self.host.delete()
        self.guest1.delete()
        self.guest2.delete()
        self.guest3.delete()
        self.video_call.delete()
        super().tearDown()

    def test_guest_list(self):
        self.assertEqual(self.video_call.guests.count(), 0)

        VideoCallGuest.objects.create(user=self.guest1,
                                      video_call=self.video_call)

        self.assertEqual(self.video_call.guests.count(), 1)
        self.assertEqual(self.video_call.guests.guest_list(), ([], self.guest1))

        VideoCallGuest.objects.create(user=self.guest2,
                                      video_call=self.video_call)

        self.assertEqual(self.video_call.guests.count(), 2)
        self.assertEqual(self.video_call.guests.guest_list(), ([self.guest1], self.guest2))

        VideoCallGuest.objects.create(user=self.guest3,
                                      video_call=self.video_call)

        self.assertEqual(self.video_call.guests.count(), 3)
        self.assertEqual(self.video_call.guests.guest_list(), ([self.guest1, self.guest2], self.guest3))

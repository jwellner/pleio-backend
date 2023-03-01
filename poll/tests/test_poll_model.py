from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from poll.models import Poll
from user.factories import UserFactory


class TestPollModelTestCase(PleioTenantTestCase):
    TITLE = "Demo poll"

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.entity = Poll.objects.create(owner=self.owner,
                                        title=self.TITLE)

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, parent_serialize):
        parent_serialize.return_value = {}
        serialized = self.entity.serialize()

        self.assertTrue(parent_serialize.called)
        self.assertEqual(serialized, {
            "title": self.TITLE
        })

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()

        self.entity.map_rich_text_fields(lambda v: "new %s" % v)

        self.assertEqual(self.entity.serialize(), before)
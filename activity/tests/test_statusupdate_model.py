from unittest import mock

from activity.models import StatusUpdate
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestStatusUpdateModelTestCase(PleioTenantTestCase):
    TITLE = "Demo blog"
    CONTENT = "Demo content"

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.entity = StatusUpdate.objects.create(owner=self.owner,
                                                  title=self.TITLE,
                                                  rich_description=self.CONTENT)

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, parent_serialize):
        parent_serialize.return_value = {}
        serialized = self.entity.serialize()

        self.assertTrue(parent_serialize.called)
        self.assertEqual(serialized, {"title": self.TITLE,
                                      "richDescription": self.CONTENT})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = f"[{self.CONTENT}]"

        self.entity.map_rich_text_fields(lambda s: f"[{s}]")
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)